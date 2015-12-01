###############################################################################
#
#  Vikasa Infinity Anugrah, PT
#  Copyright (C) 2012 Vikasa Infinity Anugrah <http://www.infi-nity.com>
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as
#  published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see http://www.gnu.org/licenses/.
#
###############################################################################

def_cash_flow_items_sql = lambda: '''
DECLARE
    acc_id RECORD;

    to_be_processed_entries VCF_TUPLE[];

    next_to_be_processed_entries VCF_TUPLE[];

    already_traversed_items INTEGER[];

    result_items VCF_TUPLE[];

    cash_in_out_items NO SCROLL CURSOR(date_start_ DATE,
                                       date_end_ DATE,
                                       company_ids_ INTEGER[],
                                       account_ids_ INTEGER[])
        FOR
         SELECT
          aml.id,
          aml.move_id,
          CASE WHEN aml.debit > aml.credit
           THEN 1::INTEGER
           ELSE 2::INTEGER
          END AS type,
          aml.date AS date,
          aml.account_id AS bank_acc_id
         FROM account_move_line aml
          INNER JOIN account_move am
           ON am.id = aml.move_id
          INNER JOIN account_account a
           ON aml.account_id = a.id
          INNER JOIN UNNEST(company_ids_) selected_company_id
           ON a.company_id = selected_company_id
          INNER JOIN UNNEST(account_ids_) selected_account_id
           ON a.id = selected_account_id
         WHERE
          aml.state = 'valid'
          AND am.state = 'posted'
          AND NOT ((aml.debit IS NULL AND aml.credit IS NULL)
                   OR (aml.debit = 0 AND aml.credit = 0))
          AND aml.date BETWEEN date_start_ AND date_end_;

    border_items NO SCROLL CURSOR(date_end_ DATE,
                                  company_ids_ INTEGER[],
                                  to_be_processed_entries_ VCF_TUPLE[],
                                  already_traversed_items_ INTEGER[])
        FOR
         SELECT
          other_items.date AS date,
          other_items.move_id AS curr_move_id,
          other_items.id AS curr_id,
          reconciled_items.move_id AS next_move_id,
          reconciled_items.id AS next_id,
          other_items.type AS type,
          other_items.bank_acc_id AS bank_acc_id
         FROM
          (
           SELECT
            aml.id, aml.move_id, entries.date, entries.type, entries.bank_acc_id,
            aml.reconcile_id, aml.reconcile_partial_id
           FROM account_move_line aml
            INNER JOIN UNNEST(to_be_processed_entries_) entries
             ON entries.id = aml.move_id
           WHERE
            NOT ((aml.debit IS NULL AND aml.credit IS NULL)
                 OR (aml.debit = 0 AND aml.credit = 0))
            AND NOT EXISTS (SELECT *
                            FROM UNNEST(already_traversed_items_) item_id
                            WHERE item_id = aml.id)
          ) other_items
          LEFT JOIN (
           SELECT aml.*
           FROM account_move_line aml
            INNER JOIN account_move am
             ON am.id = aml.move_id
            INNER JOIN UNNEST(company_ids_) selected_company_ids
             ON aml.company_id = selected_company_ids
           WHERE
            aml.state = 'valid'
            AND am.state = 'posted'
            AND NOT ((aml.debit IS NULL AND aml.credit IS NULL)
                      OR (aml.debit = 0 AND aml.credit = 0))
            AND aml.date <= date_end_
            AND NOT EXISTS (SELECT *
                            FROM UNNEST(to_be_processed_entries_) entries
                            WHERE entries.id = aml.move_id)
          ) reconciled_items
           ON (COALESCE(reconciled_items.reconcile_id,
                       reconciled_items.reconcile_partial_id)
               = COALESCE(other_items.reconcile_id,
                          other_items.reconcile_partial_id));
BEGIN
    --- Function for Cash Flow Realisation report
    result_items := ARRAY[]::VCF_TUPLE[];

    FOR acc_id IN (SELECT id FROM UNNEST(account_ids) id) LOOP
        to_be_processed_entries := ARRAY[]::VCF_TUPLE[];

        already_traversed_items := ARRAY[]::INTEGER[];

        FOR rec IN cash_in_out_items(date_start, date_end,
                                     company_ids, ARRAY[acc_id.id]) LOOP
            already_traversed_items := ARRAY_APPEND(already_traversed_items,
                                                    rec.id);
            to_be_processed_entries := ARRAY_APPEND(to_be_processed_entries,
                                                    (rec.move_id, rec.date, rec.type, rec.bank_acc_id)::VCF_TUPLE);
        END LOOP;

        WHILE ARRAY_LENGTH(to_be_processed_entries, 1) IS NOT NULL LOOP

            next_to_be_processed_entries := ARRAY[]::VCF_TUPLE[];

            FOR rec IN border_items(date_end, company_ids,
                                    to_be_processed_entries,
                                    already_traversed_items) LOOP
                already_traversed_items := ARRAY_APPEND(already_traversed_items,
                                                        rec.curr_id);
                result_items := ARRAY_APPEND(result_items,
                                             (rec.curr_id, rec.date, rec.type, rec.bank_acc_id)::VCF_TUPLE);

                IF rec.next_id IS NOT NULL THEN
                    already_traversed_items := ARRAY_APPEND(already_traversed_items,
                                                        rec.next_id);
                    result_items := ARRAY_APPEND(result_items,
                                                        (rec.next_id, rec.date, rec.type, rec.bank_acc_id)::VCF_TUPLE);
                    next_to_be_processed_entries := ARRAY_APPEND(
                        next_to_be_processed_entries,
                        (rec.next_move_id, rec.date, rec.type, rec.bank_acc_id)::VCF_TUPLE
                    );
                END IF;
            END LOOP;

            to_be_processed_entries := next_to_be_processed_entries;

        END LOOP;

    END LOOP; -- For each liquidity account_id

    RETURN QUERY (SELECT DISTINCT
                   (CASE
                     WHEN type = 1
                      THEN 'reconciled_income'
                     ELSE 'reconciled_expense'
                    END)::VARCHAR AS type,
                   id,
                   date,
                   bank_acc_id
                  FROM UNNEST(result_items) result_item
                  ORDER BY type, date, id);
END
'''

cash_flow_realization_report_sql = lambda: '''
(-- Beginning balance
 SELECT
  period.id AS period_id,
  NULL::INT AS account_id,
  aml.company_id AS com_id,
  SUM(COALESCE(aml.debit, 0.0)
      - COALESCE(aml.credit, 0.0)) AS amount,
  'beginning'::VARCHAR AS type
 FROM account_move_line aml
  INNER JOIN account_move am
   ON am.id = aml.move_id
  INNER JOIN account_account a
   ON aml.account_id = a.id
  INNER JOIN UNNEST(ARRAY[%(COMPANY_IDS)s]) selected_company_id
   ON a.company_id = selected_company_id
  INNER JOIN UNNEST(ARRAY[%(ACCOUNT_IDS)s]) selected_account_id
   ON a.id = selected_account_id
  INNER JOIN %(ROOT_COMPANY_PERIOD_ID_DATE_START_DATE_STOP_TABLE)s
   ON (aml.date >= '%(FISCAL_YEAR_DATE_START)s'
       AND aml.date < (CASE
                        WHEN ('%(DATE_START)s' BETWEEN period.date_start
                              AND period.date_stop) THEN '%(DATE_START)s'
                        ELSE period.date_start
                       END))
 WHERE
  aml.state = 'valid'
  AND am.state = 'posted'
  AND NOT ((aml.debit IS NULL AND aml.credit IS NULL)
           OR (aml.debit = 0 AND aml.credit = 0))
 GROUP BY
  period.id,
  aml.company_id
) UNION
(-- Ending balance
 SELECT
  period.id AS period_id,
  NULL::INT AS account_id,
  aml.company_id AS com_id,
  SUM(COALESCE(aml.debit, 0.0)
      - COALESCE(aml.credit, 0.0)) AS amount,
  'ending'::VARCHAR AS type
 FROM account_move_line aml
  INNER JOIN account_move am
   ON am.id = aml.move_id
  INNER JOIN account_account a
   ON aml.account_id = a.id
  INNER JOIN UNNEST(ARRAY[%(COMPANY_IDS)s]) selected_company_id
   ON a.company_id = selected_company_id
  INNER JOIN UNNEST(ARRAY[%(ACCOUNT_IDS)s]) selected_account_id
   ON a.id = selected_account_id
  INNER JOIN %(ROOT_COMPANY_PERIOD_ID_DATE_START_DATE_STOP_TABLE)s
   ON aml.date BETWEEN '%(FISCAL_YEAR_DATE_START)s' AND period.date_stop
 WHERE
  aml.state = 'valid'
  AND am.state = 'posted'
  AND NOT ((aml.debit IS NULL AND aml.credit IS NULL)
           OR (aml.debit = 0 AND aml.credit = 0))
 GROUP BY
  period.id,
  aml.company_id
) UNION
(-- Income/Expense
 SELECT
  period.id AS period_id,
  aml.account_id AS account_id,
  aml.company_id AS com_id,
  SUM(COALESCE(aml.credit, 0.0)
      - COALESCE(aml.debit, 0.0)) AS amount,
  dataset.type_ AS type
 FROM cash_flow_items('%(FISCAL_YEAR_DATE_START)s',
                      '%(DATE_STOP)s',
                      ARRAY[%(COMPANY_IDS)s],
                      ARRAY[%(ACCOUNT_IDS)s]) dataset
  INNER JOIN account_move_line aml
   ON dataset.id_ = aml.id
  INNER JOIN %(ROOT_COMPANY_PERIOD_ID_DATE_START_DATE_STOP_TABLE)s
   ON dataset.date_ BETWEEN (CASE
                              WHEN ('%(DATE_START)s' BETWEEN period.date_start
                                    AND period.date_stop) THEN '%(DATE_START)s'
                             ELSE period.date_start
                            END) AND period.date_stop
 GROUP BY
  period.id,
  dataset.type_,
  aml.account_id,
  aml.company_id
)
'''

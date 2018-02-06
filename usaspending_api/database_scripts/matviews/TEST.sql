CREATE MATERIALIZED VIEW test_award_table_matview AS
SELECT
  universal_award_matview_temp.*

  -- RUSS VARS  DONT NEED TO BE INDEXED (AWARD DBID, AWARD ID, RECIPIENT NAME, START DATE, END DATE, AWARD AMOUNT, AWARDING AGENCY, AWARDING SUB AGENCY, CONTRACT AWARD TYPE)
  --"awards"."id"  -- duplicate of "transaction_normalized"."award_id"
    --  "awards"."fain",
    --  "awards"."uri",
    --  "awards"."piid",
  "awards"."recipient"."name"                           AS award_recipient_name,
  "awards"."period_of_performance_start_date"           AS award_period_of_performance_start_date,        -- start date
  "awards"."period_of_performance_current_end_date"     AS award_period_of_performance_current_end_date,  -- end date
    --"awards"."total_obligation", --duplicate
  "awards"."awarding_agency"."toptier_agency"."name"    AS award_toptier_agency_name,
  "awards"."awarding_agency"."subtier_agency"."name"    AS award_subtier_agency_name,
  "awards"."type_description"                           AS award_type_description,
  --  "awards"."type" -- "transaction_normalized"."type",
FROM
  "universal_award_matview_temp"

LEFT OUTER JOIN
  "awards" ON ("universal_award_matview_temp"."award_id" = "awards"."id")

--GRANT SELECT ON universal_transaction_matview TO readonly
;

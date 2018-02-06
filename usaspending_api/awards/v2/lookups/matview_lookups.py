award_contracts_mapping = {
    'Award ID': 'piid',
    'Recipient Name': 'recipient_name',
    'Start Date': 'period_of_performance_start_date',
    'End Date': 'period_of_performance_current_end_date',
    'Award Amount': 'total_obligation',
    'Contract Award Type': 'type_description',
    'Awarding Agency': 'awarding_toptier_agency_name',
    'Awarding Sub Agency': 'awarding_subtier_agency_name',
    'Funding Agency': 'funding_toptier_agency_name',  # Leave in for possible future use
    'Funding Sub Agency': 'funding_subtier_agency_name',  # Leave in for possible future use
}

grant_award_mapping = {
    'Award ID': 'fain',
    'Recipient Name': 'recipient_name',
    'Start Date': 'period_of_performance_start_date',
    'End Date': 'period_of_performance_current_end_date',
    'Award Amount': 'total_obligation',
    'Awarding Agency': 'awarding_toptier_agency_name',
    'Awarding Sub Agency': 'awarding_subtier_agency_name',
    'Award Type': 'type_description',
    'Funding Agency': 'funding_toptier_agency_name',  # Leave in for possible future use
    'Funding Sub Agency': 'funding_subtier_agency_name',  # Leave in for possible future use
}

loan_award_mapping = {
    'Award ID': 'fain',
    'Recipient Name': 'recipient_name',
    'Issued Date': 'action_date',
    'Loan Value': 'face_value_loan_guarantee',
    'Subsidy Cost': 'original_loan_subsidy_cost',
    'Awarding Agency': 'awarding_toptier_agency_name',
    'Awarding Sub Agency': 'awarding_subtier_agency_name',
    'Funding Agency': 'funding_toptier_agency_name',  # Leave in for possible future use
    'Funding Sub Agency': 'funding_subtier_agency_name',  # Leave in for possible future use
}

direct_payment_award_mapping = {
    'Award ID': 'fain',
    'Recipient Name': 'recipient_name',
    'Start Date': 'period_of_performance_start_date',
    'End Date': 'period_of_performance_current_end_date',
    'Award Amount': 'total_obligation',
    'Awarding Agency': 'awarding_toptier_agency_name',
    'Awarding Sub Agency': 'awarding_subtier_agency_name',
    'Award Type': 'type_description',
    'Funding Agency': 'funding_toptier_agency_name',  # Leave in for possible future use
    'Funding Sub Agency': 'funding_subtier_agency_name',  # Leave in for possible future use
}

other_award_mapping = {
    'Award ID': 'fain',
    'Recipient Name': 'recipient_name',
    'Start Date': 'period_of_performance_start_date',
    'End Date': 'period_of_performance_current_end_date',
    'Award Amount': 'total_obligation',
    'Awarding Agency': 'awarding_toptier_agency_name',
    'Awarding Sub Agency': 'awarding_subtier_agency_name',
    'Award Type': 'type_description',
    'Funding Agency': 'funding_toptier_agency_name',  # Leave in for possible future use
    'Funding Sub Agency': 'funding_subtier_agency_name',  # Leave in for possible future use
}

award_assistance_mapping = {**grant_award_mapping, **loan_award_mapping, **direct_payment_award_mapping,
                            **other_award_mapping}
non_loan_assistance_award_mapping = assistance_award_mapping = {**grant_award_mapping, **direct_payment_award_mapping,
                                                                **other_award_mapping}


# transaction based mappings for award table

transaction_contracts_mapping = {
    'Award ID': 'piid',
    'Recipient Name': 'award_recipient_name',
    'Start Date': 'award_period_of_performance_start_date',
    'End Date': 'award_period_of_performance_current_end_date',
    'Award Amount': 'total_obligation',
    'Contract Award Type': 'award_type_description',
    'Awarding Agency': 'award_awarding_toptier_agency_name',
    'Awarding Sub Agency': 'award_awarding_agency_name',
    # 'Funding Agency': 'award_funding_toptier_agency_name',  # Leave in for possible future use
    # 'Funding Sub Agency': 'award_funding_subtier_agency_name',  # Leave in for possible future use'Award ID': 'piid',
    # other potential maps
    # 'Recipient Name': 'awards__recipient_name',
    # 'Start Date': 'awards__period_of_performance_start_date',
    # 'End Date': 'awards__period_of_performance_current_end_date',
    # 'Award Amount': 'total_obligation',
    # 'Contract Award Type': 'awards__type_description',
    # 'Awarding Agency': 'awards__awarding_toptier_agency_name',
    # 'Awarding Sub Agency': 'awards__awarding_subtier_agency_name',
    # 'Funding Agency': 'awards__funding_toptier_agency_name',  # Leave in for possible future use
    # 'Funding Sub Agency': 'awards__funding_subtier_agency_name',  # Leave in for possible future use
}

grant_transaction_mapping = {
    'Award ID': 'fain',
    'Recipient Name': 'awards__recipient__name',
    'Start Date': 'awards__period_of_performance_start_date',
    'End Date': 'awards__period_of_performance_current_end_date',
    'Award Amount': 'awards__total_obligation',
    'Awarding Agency': 'awards__awarding_toptier_agency_name',
    'Awarding Sub Agency': 'awards__awarding_subtier_agency_name',
    'Award Type': 'awards__type_description',
    'Funding Agency': 'awards__funding_toptier_agency_name',  # Leave in for possible future use
    'Funding Sub Agency': 'awards__funding_subtier_agency_name',  # Leave in for possible future use
}

loan_transaction_mapping = {
    'Award ID': 'fain',
    'Recipient Name': 'awards__recipient__name',
    'Issued Date': 'awards__action_date',
    'Loan Value': 'awards__face_value_loan_guarantee',
    'Subsidy Cost': 'awards__original_loan_subsidy_cost',
    'Awarding Agency': 'awards__awarding_toptier_agency_name',
    'Awarding Sub Agency': 'awards__awarding_subtier_agency_name',
    'Funding Agency': 'awards__funding_toptier_agency_name',  # Leave in for possible future use
    'Funding Sub Agency': 'awards__funding_subtier_agency_name',  # Leave in for possible future use
}

direct_payment_transaction_mapping = {
    'Award ID': 'fain',
    'Recipient Name': 'awards__recipient__name',
    'Start Date': 'awards__period_of_performance_start_date',
    'End Date': 'awards__period_of_performance_current_end_date',
    'Award Amount': 'awards__total_obligation',
    'Awarding Agency': 'awards__awarding_toptier_agency_name',
    'Awarding Sub Agency': 'awards__awarding_subtier_agency_name',
    'Award Type': 'awards__type_description',
    'Funding Agency': 'awards__funding_toptier_agency_name',  # Leave in for possible future use
    'Funding Sub Agency': 'awards__funding_subtier_agency_name',  # Leave in for possible future use
}

other_transaction_mapping = {
    'Award ID': 'fain',
    'Recipient Name': 'awards__recipient__name',
    'Start Date': 'awards__period_of_performance_start_date',
    'End Date': 'awards__period_of_performance_current_end_date',
    'Award Amount': 'awards__total_obligation',
    'Awarding Agency': 'awards__awarding_toptier_agency_name',
    'Awarding Sub Agency': 'awards__awarding_subtier_agency_name',
    'Award Type': 'awards__type_description',
    'Funding Agency': 'awards__funding_toptier_agency_name',  # Leave in for possible future use
    'Funding Sub Agency': 'awards__funding_subtier_agency_name',  # Leave in for possible future use
}

transaction_assistance_mapping = {**grant_transaction_mapping, **loan_transaction_mapping,
                                  **direct_payment_transaction_mapping,
                                  **other_transaction_mapping}
non_loan_assistance_transaction_mapping = assistance_transaction_mapping = {**grant_transaction_mapping,
                                                                            **direct_payment_transaction_mapping,
                                                                            **other_transaction_mapping}


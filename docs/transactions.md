# Transactions

```{list-table} Assets

* - Field Name
  - Required
  - Data Type
  - Default
  - Description
* - `name`
  - Y
  - string
  - N/A
  - Name of transaction
* - `amount`
  - Y
  - decimal
  - N/A
  - Amount to withdraw and/or deposit
* - `source`
  - N
  - string
  - N/A
  - Name of an [Asset](/docs/assets.md) to withdraw from.
* - `destination`
  - N
  - string
  - N/A
  - Name of an [Asset](/docs/assets.md) to deposit to.
* - `interest_rate`
  - N
  - string
  - 0.0 interest rate
  - Name of an [Interet Rate](/docs/interest_rate.md) to apply to `amount` based on time since simulation start.
* - `income_taxable`
  - N
  - boolean
  - False
  - Transaction amount is considered taxable income.
* - `fed_income_tax_payment`
  - N
  - boolean
  - False
  - **No `detination if `True`, must have `source`.** Transaction amount will be deducted from federal tax bill.
* - `state_income_tax_payment`
  - N
  - boolean
  - False
  - **No `detination if `True`, must have `source`.** Transaction amount will be deducted from state tax bill.
* - `amount_remaining_balance`
  - N
  - boolean
  - False
  - **Requires a `source`.** Withdraws the remaining balance of the `source`.
* - `amount_above`
  - N
  - decimal
  - None
  - **Requires a `source`.** Withdraws the remaining balance above the defined amount.
* - `frequency`
  - N
  - string
  - `monthly`
  - **Must be one of `monthly`, `daily`, `biweekly`, `yearly`, or `weekly`** Frequency with which transaction will occur.
* - `end`
  - N
  - string
  - None
  - Name of an [Important Date](/docs/simulation.md) on which date the transaction will cease to execute. 
```

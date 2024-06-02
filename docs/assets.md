# Assets

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
  - Name of asset
* - `balance`
  - N
  - decimal
  - 0.00
  - Starting balance of asset
* - `category`
  - N
  - string
  - None
  - Grouping of assets for easier results viewing
* - `min_withdrawal_date`
  - N
  - date
  - None
  - Minimum date at which funds can be withdrawn from asset.  Attempted withdrawals prior to this date will end simulation with an error.
```
# Example Stories

## Story #1 - Basics

This documentation will walk through the creation of the plan in `example_plan`.

First, we will start with a single file: `plan_1.yml`.

The example below should be considered "inflation adjusted".  It assumes
that everything will increase proportionally with inflation, e.g. income
and expenses.  This means that all interest rates used should have the
effects of inflation removed.

This example does not cover:

1. Inflation
2. Mortgages
3. Taxes
4. Retirement

Examples in the following sections will cover these features/topics.

### Income, Assets, and Basic Transactions

Most financial stories start with income.  Income occurs in the form
of transactions which have both a source and destination.  For income
the source is not ourselves, therefore it can be ignored, but the destination
is important.  In the planner, the `ActionManager` is responsible for
executing transactions which result in the modification of the balance
of `assets` and/or `debts`.

For this example, we will assume two sources of income with a single
bank account destination.

```yaml
action_manager:
    assets:
        - name: Checking Account Green
          type: asset
    transactions:
        - name: Income Dog
          base_amount: 5000.00
          destination: Checking Account Green
        - name: Income Cat
          base_amount: 2500.00
          destination: Checking Account Green
```

Let's run this simulation:

```bash
planner example_plan/plan.yml
```

In the action `action_log.csv` we can see both transactions occuring
each day and the associated balance in `asset_log.csv` rising very
rapidly.

Typical job income is not paid out on a daily basis.  Let's say `Income Dog`
is monthly, and `Income Cat` is Biweekly (paid every two weeks).

```yaml
# previous parts unchanged, but removed for brevity
    transactions:
        - name: Income Dog
          base_amount: 5000.00
          destination: Checking Account Green
          frequency: monthly
        - name: Income Cat
          base_amount: 2500.00
          destination: Checking Account Green
          frequency: biweekly
```

Now in `action_log.csv` we see `Income Dog` occuring on the 1st of each
month and `Income Cat` occuring every 14 days.

### Dates

By default the planner makes many assumptions, e.g.

- Duration of the simulation
- Simulation start date
- Date of transactions

This can lead to some variability depending on when the simulation is
executed, e.g. where and how many biweekly pay events occur in a month.
We can make the simulation more predictable by providing some specific
date information such as simulation start date (in form `YYYY-MM-DD`):

```yaml
start: 2025-01-01
end: 2074-12-31
action_manager:
    assets:
        - name: Checking Account Green
          type: asset
    transactions:
        - name: Income Dog
          base_amount: 5000.00
          destination: Checking Account Green
          frequency: monthly
        - name: Income Cat
          base_amount: 2500.00
          destination: Checking Account Green
          frequency: biweekly
```

Since the planner is running a day by day simulation, it is desirable
to place the transactions as accurately as possible.  Using `first_date`
we can set the reference for the `frequency`:

```yaml
# previous parts unchanged, but removed for brevity
    transactions:
        - name: Income Dog
          base_amount: 5000.00
          destination: Checking Account Green
          frequency: monthly
          first_date: 2025-01-28 # Toward the end of the month, not greater than 28
        - name: Income Cat
          base_amount: 2500.00
          destination: Checking Account Green
          frequency: biweekly
          first_date: 2025-01-03 # First Friday
```

### Expenses (Transactions)

If life was all income, we would not need a planner.  We
add them to the same `transactions` section as the income,
but expenses only have a source and not a destination.

$400 per month in groceries:

```yaml
# previous parts unchanged, but removed for brevity
    transactions:
        - name: Income Dog
          base_amount: 5000.00
          destination: Checking Account Green
          frequency: monthly
          first_date: 2025-01-28 # Toward the end of the month, not greater than 28
        - name: Income Cat
          base_amount: 2500.00
          destination: Checking Account Green
          frequency: biweekly
          first_date: 2025-01-03 # First Friday
        - name: Groceries
          base_amount: 400.00
          source: Checking Account Green
          frequency: monthly
          first_date: 2025-01-28 # Let's buy groceries on pay day
```

Now we see some negative `amount`s in our `action_log.csv`, and we can also
see the effect in the balances in the `asset_log.csv`.  Let's add a few
expenses just to spice things up:

```yaml
# previous parts unchanged, but removed for brevity
        - name: Rent
          base_amount: 2000.00
          source: Checking Account Green
          frequency: monthly
          first_date: 2025-01-28 # On pay day again
        - name: Netflix
          base_amount: 20.00
          source: Checking Account Green
          frequency: monthly
          first_date: 2025-01-15 # Somewhere in the middle
        - name: Electricity
          base_amount: 80.00 # An average over the year to keep things simple
          source: Checking Account Green
          frequency: monthly
          first_date: 2025-01-20
        - name: Water
          base_amount: 70.00 # An average over the year to keep things simple
          source: Checking Account Green
          frequency: monthly
          first_date: 2025-01-20
        - name: Natural Gas
          base_amount: 70.00 # An average over the year to keep things simple
          source: Checking Account Green
          frequency: monthly
          first_date: 2025-01-20
```

We can also do non-monthly expenses:
```yaml
        - name: Car Gas
          base_amount: 70.00 # An average over the year to keep things simple
          source: Checking Account Green
          frequency: weekly
```

### Asset Starting Balance

Uh-oh, trying to fill up with gas on the first day of the simulation
prior to any pay days.  Let's go back have a starting balance on that
checking account

```yaml
    assets:
        - name: Checking Account Green
          type: asset
          starting_balance: 5000.00
```

That `action_log.csv` is looking pretty busy.

### Infrequent expenses

What about those big bills that don't come very frequently, e.g.
insurance every 6 months or once a year, property taxes.

```yaml
# previous parts unchanged, but removed for brevity
    transactions:
      # skipping previous expenses above for brevity
      - name: Car Insurance
        base_amount: 1000.00
        source: Checking Account Green
        frequency: monthly
        every_x_periods: 6 # every 6 months
        first_date: 2025-04-10 # In April and Oct
      - name: Renters Insurance
        base_amount: 1500.00
        source: Checking Account Green
        frequency: yearly
        first_date: 2025-08-08 # Yearly in August
```

It is hard to see those in the busy `action_log.csv`, but if you search
you will find them.

We can even do very infrequent expenses like:

```yaml
# previous parts unchanged, but removed for brevity
    transactions:
      # skipping previous expenses above for brevity
      - name: Washing Machine Replacement
        base_amount: 1000.00
        source: Checking Account Green
        frequency: yearly
        every_x_periods: 10 # new washer every 10 years
        first_date: 2029-01-01 # First replacement new years! 2029
```

### Timeframe Expenses

Some expenses don't last forever and some do not start until later.
Maybe you have baby (and associated day care), and you you have to pay
for Pre-K school after that.

```yaml
# previous parts unchanged, but removed for brevity
    transactions:
      # skipping previous expenses above for brevity
      - name: Day Care
        base_amount: 500.00
        source: Checking Account Green
        frequency: monthly
        first_date: 2025-01-05
        end: 2027-07-31 # Kid will be 4 and ready for Pre-K!
      - name: Pre-K
        base_amount: 300.00 # Thankfully Pre-K is a little cheaper
        source: Checking Account Green
        frequency: monthly
        first_date: 2027-08-05 # First replacement new years! 2029
        start: 2027-07-31 # Start after day care
        end: 2028-07-31 # Ends after a year
```

We can see the `Day Care` expenses end in July 2027 and the Pre-K expenses
start in August 2027 in the `action_log.csv`.  And Pre-K expenses only last
for 1 year.

### Account Transfers

Let's try to save some money for that little kid's future.  Let's make a
new account (`asset`) and a transaction that has both a `source` and
`destination`.

```yaml
# previous parts unchanged, but removed for brevity
action_manager:
    assets:
        # skipping previous expenses above for brevity
        - name: Kid Education Savings
          type: asset
    transactions:
      - name: Kid Education Savings Transfer
        base_amount: 100.00
        source: Checking Account Green
        destination: Kid Education Savings
        frequency: monthly
        first_date: 2025-01-28 # End of the month
        end: 2045-07-31 # Let's give them until they are in their earlier 20's
```

Alright, we can see in the `asset_log.csv` you will have saved $24,700 by the 
time you stop.  In the `action_log.csv` we can see the withdrawal from checking
followed by the deposit each time.

### Interest

We are usually really hoping that by putting away that money early
interest will work in our favor.  Although slightly unintuitive,
interest is just another `transaction`.  Like income,
these only have a `destination`.

```yaml
interest_rates:
  Market:
    year_rate_percentage: 5.0 # 5% (a common choice for inflation adjusted)
    interest_type: basic
# previous parts unchanged, but removed for brevity
    transactions:
      # skipping previous expenses above for brevity
      - name: Kid Education Savings Maturation
        maturation: True
        interest_rate: Market
        destination: Kid Education Savings
```

Now the `action_log.csv` is getting very busy.

## Story #2 - Mortgages, Debts and Inflation

**Story #2 is a new example plan (`example_plan/plan_2.yaml`) and
does not build on Story #1 for simplicity.**

Mortgages are obviously complicated from the calculation of each
payment's principal and interest which is paying down a balance
that does not necessarily match the value of the home that was
purchased.  Mortgages will also be our example to show why
we might want to include the extra realism of inflation in
our simulation since a fixed rate mortgage payment does not
increase with inflation.

### Debts and Mortgage

First, a mortgage is payment plan to pay back a loan which is a
debt.  Let's capture the debt which would be the remaining balance
on the mortgage.  Let's say the original loan was $350,000,
and the current remaining balance is $350,000, i.e. no payments
have been made.

**Note the negative balance on the debt.**

```yaml
start: 2025-01-01
end: 2074-12-31
action_manager:
    assets:
        - name: Home Loan
          type: debt
          starting_balance: -350000.00
```

Now we obviously need an account from which to make payments:

```yaml
start: 2025-01-01
end: 2074-12-31
action_manager:
    assets:
        - name: Checking Account Green
          type: asset
          starting_balance: 700000.00
        - name: Home Loan
          type: debt
          starting_balance: -350000.00
```

A mortgage is defined similarly to a normal transaction, i.e.
it has a source, destination and name, but it has has additional
required fields:

- `name` - Name of the mortgage.
- `source` - Source asset name from which payments will be made.
- `destination` - Debt name to be paid down, i.e. the remaining balance
- `loan_amount` - The original loan amount regardless of remaining balance.
- `loan_rate` - Yearly interest rate
- `term_months` - Original loan term length in months, e.g. 30 years = 360 months

The frequency of mortgage payments is Monthly and cannot be
changed.

```yaml
start: 2025-01-01
end: 2074-12-31
action_manager:
    assets:
        - name: Checking Account Green
          type: asset
          starting_balance: 700000.00
        - name: Home Loan
          type: debt
          starting_balance: -350000.00
    transactions:
        - name: Home Mortgage
          source: Checking Account Green
          destination: Home Loan
          loan_amount: 350000.00
          loan_rate: 5.0
          term_months: 360
```

In the `action_log.csv` we can see 3 transactions each month:

1. A debit of the principal amount from the source
2. A debit of the interest amount from the source
3. A deposit of the principal amount at the destination (the debt)

Adding #1 and #2 will produce the normal mortgage payment one would make
(minus any mortgage insurance and taxes in escrow).
The amount of the principal and interest portions are dynamically
calculated based on the remaining balance of the debt and the loan
terms.

In the `asset_log.csv`, we can see the balance of the source reducing
at a faster rate, and we can see the balance of the destination increasing
toward $0 at a slower rate.  We see the debt balance reach $0 exactly
30 years from the start of the simulation which was the start
of the payments.  Also of note, that it took almost $675,000 from the
account to pay the $350,000 debt.

#### Extra Principal Payments

Making extra payments toward the principal of the loan can reduce
the total interest paid.  Extra payments can be added as simple transactions:

```yaml
start: 2025-01-01
end: 2074-12-31
action_manager:
    assets:
        - name: Checking Account Green
          type: asset
          starting_balance: 700000.00
        - name: Home Loan
          type: debt
          starting_balance: -350000.00
    transactions:
        - name: Home Mortgage
          source: Checking Account Green
          destination: Home Loan
          loan_amount: 350000.00
          loan_rate: 5.0
          term_months: 360
        - name: Home Loan Extra Principal
          source: Checking Account Green
          destination: Home Loan
          base_amount: 500.00
          frequency: monthly
          only_if_destination_balance_negative: true
```

The `only_if_destination_balance_negative` setting assures that payments
will only be made while the loan balance is negative.

We can see in the logs that by paying an extra $500 per month, the loan
was paid off about 11 years early and saved about $132,000 compared
to simply paying the scheduled payment.

#### In Progress Mortgages

The planner can handle mortgages that are in progress at the start
of the simulation.  The only change that is necessary is to populate
an up to date remaining balance on the debt.

```yaml
start: 2025-01-01
end: 2074-12-31
action_manager:
    assets:
        - name: Checking Account Green
          type: asset
          starting_balance: 700000.00
        - name: Home Loan
          type: debt
          starting_balance: -300000.00
    transactions:
        - name: Home Mortgage
          source: Checking Account Green
          destination: Home Loan
          loan_amount: 350000.00
          loan_rate: 5.0
          term_months: 360
```

**Only the debt `starting_balance` was changed from the previous
example.**

We can see the debt is repaid much earlier in the `asset_log.csv`: year 21
of the simulation.

### Renting, Inflation and Interest

A few reasons one often chooses to purchase a home over renting:

1. Homes typically appreciate in value
2. Once the mortgage is paid, housing expenses go down.
3. Rents continue to rise with inflation.

We cannot evaluate these effects without taking into account
inflation.

First, let's look at how rent payments may inflate over time.

```yaml
start: 2025-01-01
end: 2074-12-31
interest_rates:
  Inflation: 
    interest_type: basic
    year_rate_percentage: 3.0
action_manager:
    assets:
        - name: Checking Account Green
          type: asset
          starting_balance: 700000.00
    transactions:
        - name: Rent
          source: Checking Account Green
          base_amount: 1500.00
          interest_rate: Inflation
          frequency: monthly
```

Rent starting in the simulation at $1,500 per month increasing
with inflation (3% per year).  Taking a look at the `action_log.csv`
we can see that the first payment was $1,500, but the payment
increases each time.  The first payment of 2026 is $1,545 (3% more).
This simulation actually ends early (after only 25 years) because we
run out of money
in 2050 where the rent payment has increased to $3,212.44.  This
seems exceptionally concerning in this simple simulation. 
Fortunately, any type of income will also be increasing with
inflation, but it also important that we not simply leave $700,000
in an account that does not appreciate (or appreciates VERY slowly
like many checking accounts).  Let's see the difference if the
account is appreciating with inflation.

```yaml
start: 2025-01-01
end: 2074-12-31
interest_rates:
  Inflation: 
    interest_type: basic
    year_rate_percentage: 3.0
action_manager:
    assets:
        - name: Checking Account Green
          type: asset
          starting_balance: 700000.00
    transactions:
        - name: Rent
          source: Checking Account Green
          base_amount: 1500.00
          interest_rate: Inflation
          frequency: monthly
        - name: Checking Account Green Maturation
          maturation: True
          interest_rate: Inflation
          destination: Checking Account Green
```

Our money lasted 13 additional years!  Let's see if we were
to get historical stock market returns:

```yaml
start: 2025-01-01
end: 2074-12-31
interest_rates:
  Inflation: 
    interest_type: basic
    year_rate_percentage: 3.0
  Market: 
    interest_type: basic
    year_rate_percentage: 10.0
action_manager:
    assets:
        - name: Checking Account Green
          type: asset
          starting_balance: 700000.00
    transactions:
        - name: Rent
          source: Checking Account Green
          base_amount: 1500.00
          interest_rate: Inflation
          frequency: monthly
        - name: Checking Account Green Maturation
          maturation: True
          interest_rate: Market
          destination: Checking Account Green
```

Now, not only does the simulation complete, but the account
ends with $50,000,000.

### Mortgage Revisited with Inflation

The appreciation of a home is dependent on many factors
many of which are at best difficult to predict.  Assuming
appreciation with inflation is a relatively conservative
approach.  The previous examples did not account for the
asset gained when intiating a loan, so let's fix that.

```yaml
start: 2025-01-01
end: 2074-12-31
interest_rates:
  Inflation: 
    interest_type: basic
    year_rate_percentage: 3.0
action_manager:
    assets:
        - name: Checking Account Green
          type: asset
          starting_balance: 700000.00
        - name: Home Loan
          type: debt
          starting_balance: -350000.00
        - name: Home
          type: asset
          starting_balance: 450000.00 # Assumes a 25% down payment
    transactions:
        - name: Home Mortgage
          source: Checking Account Green
          destination: Home Loan
          loan_amount: 350000.00
          loan_rate: 5.0
          term_months: 360
        - name: Home Maturation
          maturation: True
          interest_rate: Inflation
          destination: Home
```

Even though the home is a physical asset, appreciating its value
is once again accomplished with a transaction.

We can see in the `asset_log.csv` that when the loan reaches a
$0 balance, the home has appreciated to over $1,000,000.

**The examples above could be interpretted as a clear superiority
for the mortgage vs renting, but please do not forget that property
taxes and home maintanence are costs that will continue forever
with inflation.**

## Story #3 - Taxes and Retirement

For basic simulations, taxes can be represented as a simple
transaction.

## Story #4 - Other Tricks
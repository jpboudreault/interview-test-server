# Deductions and credits

Both lower your tax, at different steps.

- **Deduction:** subtracted from your **income** before the brackets apply, up to `max_amount`.
- **Credit:** subtracted from the **tax** once it's calculated. A non-refundable credit (`"refundable": false`) can bring the tax down to $0 but never below it.

## The order

1. Start with the income.
2. Subtract the deductions, each capped at its `max_amount`.
3. Apply the brackets to what's left.
4. Subtract the credits, with a floor of $0.

## The endpoint

`GET /tax-calculator/tax-year/2022/credits`

```json
{
  "deductions": [
    { "code": "RRSP", "description": "...", "max_amount": 29210 }
  ],
  "credits": [
    { "code": "BASIC_PERSONAL", "description": "...", "amount": 2159.7, "refundable": false }
  ]
}
```

## Example: 2022, $80,000 income, $5,000 RRSP contribution

The 2022 brackets are 15% up to $50,197 and 20.5% from $50,197 to $100,392.

| Step | Calculation | Result |
|---|---|---|
| Income | | $80,000.00 |
| RRSP deduction | $5,000 is under the $29,210 cap | − $5,000.00 |
| Taxable income | | $75,000.00 |
| First bracket | $50,197 × 15% | $7,529.55 |
| Second bracket | ($75,000 − $50,197) × 20.5% | $5,084.62 |
| Tax before credits | | $12,614.17 |
| Basic personal credit | | − $2,159.70 |
| **Tax owed** | | **$10,454.47** |

With no RRSP contribution and no credit, the tax on $80,000 would be $13,639.16.

## Edge cases

- **Contribution over the cap:** a $40,000 RRSP contribution only deducts $29,210.
- **Credit bigger than the tax:** on $12,000 of income the tax is $1,800, so the $2,159.70 credit brings it to $0, not −$359.70.

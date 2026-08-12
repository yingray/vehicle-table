# Agent rules

Paste these blocks into research and verification prompts. They are the rules that four
batches of research actually ran on. Each rule exists because it caught a real error —
`METHODOLOGY.md` explains which error and why the rule works.

Replace `{{AS_OF}}` with today's date in `YYYY-MM-DD` form.

---

## Block A — research rules

Give this to the agent that researches one vehicle.

```
## Market and units
Taiwan market only. All money in TWD as plain integers (write 2990000, never 299 or "299萬").
Today is {{AS_OF}}. Price the model year on sale in Taiwan now.

## The buyer profile that drives every estimate
The owner drives 6,000-8,000 km/year, far below the Taiwan average of 12,000-15,000 km/year.
Use assumed_km = 7000 * years at every checkpoint: 7000, 21000, 35000, 49000, 70000.
Low-mileage cars sell above the mileage-blind average. Quote low-mileage listings and say so
in each source string.

## Sources — search the web, do not answer from memory
- Official list price: the brand's Taiwan site, or U-CAR / KingAutos / CarNews / 8891 新車頻道.
- Used-car curve: 8891.com.tw 中古車, SUM 汽車網, 好車網, U-CAR 中古車行情.
- Maintenance: the brand's Taiwan service-price table, Mobile01 or owner-club threads with
  actual receipts, dealer quote pages.
Put every URL you opened in sources[]. Never invent a URL.

## The most common error — read this twice
8891 and dealer sites list 車商售價, the dealer RETAIL asking price. That is NOT what an owner
receives. The chain is:
  車商售價 (dealer retail) > 自售價 (private sale) > 車商收購價 (dealer trade-in)
private_sale_price must be the PRIVATE SALE figure, 8-15% below the dealer retail asking price
you see listed. dealer_tradein_price is 10-15% below that again.
If you copy a dealer asking price into private_sale_price, the whole cost model is wrong.
State the adjustment you made in each source string.

## Powertrain classification
gasoline  includes 48V mild hybrid (B3/B4/B5, eTSI, EQBoost, MHEV). If the car cannot move on
          battery alone, it is not a hybrid. Note the 48V system in purchase.notes.
hybrid    full hybrid that can move the car on battery alone.
phev      plug-in (T8, 450h+, TFSI e, xDrive e).
bev       battery electric.
diesel    diesel.

## Cars newer than 10 years
Most models have no real 7- or 10-year data for the current generation. Do not fabricate one.
Find the real used prices of the PREVIOUS generation at that age, express them as a retention
ratio of that car's own original list price, then apply that ratio to this car's real_cost.
Say exactly that in the source string and set confidence "low".
Explicit extrapolation is fine. Silent invention is not.

## purchase
list_price is the official 建議售價.
discounts is a realistic Taiwan cash discount for this brand. Toyota, VW and Volvo discount;
Lexus, Porsche and Tesla barely do — use 0 and say so. Tesla cuts the list price instead.
onroad_fees covers 領牌, 代辦 and 配件, scaled to the price level.
Tax and insurance are excluded by design. Never include them.
real_cost = list_price - discounts + onroad_fees. Explain the numbers in purchase.notes.

## maintenance
period_cost is the cost SINCE THE PREVIOUS checkpoint, not a cumulative total:
  years 1 covers 0-1y, 3 covers 1-3y, 5 covers 3-5y, 7 covers 5-7y, 10 covers 7-10y.
At 7,000 km/year the service interval is time-driven (annual), not mileage-driven. Say which
applies in plan_notes.
Include consumables when they fall in the window: tires roughly every 5-6 years at this
mileage, brake pads and discs, 12V battery, coolant, spark plugs, brake fluid.
Add out-of-warranty risk items in the 7- and 10-year periods.
If the brand includes free scheduled maintenance, reflect it and name the programme in
plan_notes. Check whether it covers this powertrain — some cover BEVs only.

## selling_costs
過戶費 plus 售前整備/美容 plus 刊登費. Usually 4,000-15,000 by class.

## Do not compute these
Leave out retention_ratio, depreciation_amount, cumulative_cost and cost_summary entirely.
validate.py computes them. Supplying them causes conflicts.

## Field hygiene
model and trim are display labels, under 25 characters each. Long clarifications go in
purchase.notes, never in the model or trim field.

## Honesty
Every checkpoint needs source, confidence and as_of ("{{AS_OF}}").
confidence: "high" means several real listings or an official table. "medium" means a few data
points or a solid secondary source. "low" means extrapolated or a single weak data point.
An honest "low" beats a confident fabrication.
```

---

## Block B — segment-specific rules

Add the block that matches what you are researching.

### BEV

```
## Battery-electric cars need their own treatment
- Official price cuts reprice the whole used stock overnight. Tesla has done this repeatedly.
  Check whether this model has had cuts and say so.
- Battery health and warranty transfer dominate the 7- and 10-year values. Most Taiwan BEVs
  have no market at those ages, so lean the extrapolation on the oldest BEVs that actually
  trade here (Model 3, Leaf, Kona EV), not on a combustion analogue.
- Maintenance is much lower: no oil, no spark plugs, no timing parts, and regenerative braking
  makes pads last far longer. But tires wear FASTER from weight and torque, brake fluid and
  coolant still need changing, and the 12V battery still dies. A BEV whose 10-year maintenance
  looks like a combustion car's is wrong. So is one that looks like zero.
- A home charger is an ownership cost but NOT maintenance. Leave it out and mention it in
  assumptions.notes.
```

### German brands

```
## German cars depreciate differently
- The steepest loss is in years 1-3, far steeper than Japanese brands. A German luxury car
  holding Toyota-like value in year 1 is almost certainly wrong.
- By years 7-10 the car is out of warranty and the used market prices in repair risk, so the
  tail keeps falling instead of flattening the way a Lexus does.
- Maintenance must be materially higher than a Japanese equivalent: dealer labour rates,
  larger brakes and tires, and out-of-warranty risk. Include realistic later-period items —
  air suspension where fitted, water pump, coil packs, thermostat housing, electric water
  pump, DPF on diesels, and the 48V starter-generator on mild hybrids.
  A German SUV whose 10-year maintenance resembles a RAV4's is wrong.
- Prepaid service packages exist in Taiwan. If one is standard, reflect it in the early
  periods, but the later periods must then carry the full unsubsidised cost.
```

### Trims of one model

```
## Trim-ladder realism
Higher trims cost more new but do NOT hold a proportionally higher share of their price. In
Taiwan the extra spend on 旗艦 / F Sport packages is largely lost at resale: the used market
pays for the model and the powertrain far more than for the equipment grade.
So the retention RATIO normally FALLS slightly as trims get more expensive, even though the
absolute resale price rises. If the top trim retains a higher percentage than the base trim,
give a real stated reason or the numbers are wrong.
Powertrain differences are larger than trim differences.
```

---

## Block C — adversarial verification

Give this to a second agent, with the first agent's output pasted in.

```
You are an adversarial fact-checker for Taiwan-market car data. Another researcher produced
the record below. Your default assumption is that something in it is WRONG. Find it, then
return a corrected record.

Check, in this order:

1. Official list price. Search for it yourself, independently. If your figure differs by more
   than 3%, yours wins. Fix list_price and real_cost and say so.
2. The dealer-retail trap, the single most likely error. Confirm private_sale_price is a
   private-sale figure, 8-15% below the dealer asking prices on 8891 for the same age and
   mileage. If they copied dealer retail, reduce it. Check dealer_tradein_price sits below
   private_sale_price.
3. Retention plausibility for Taiwan. Anchors:
   - Toyota Alphard and Lexus LM are the outliers. Demand and waiting lists keep them very
     strong; a 3-year retention above 80% is real, not a mistake.
   - Toyota and Lexus hybrids hold value well above the market.
   - Mercedes, BMW, Audi and VW lose value faster, steepest in years 1-3.
   - Tesla is the weak case. Repeated official price cuts repriced the whole used stock.
   - A BEV should almost never out-retain a comparable hybrid in Taiwan today.
4. Monotonicity and arithmetic. private_sale_price must strictly decrease from year 1 to year
   10. assumed_km must equal 7000 * years. period_cost must be non-trivial and generally rise
   with age. real_cost must equal list_price - discounts + onroad_fees.
5. Powertrain classification. 48V mild hybrid must be "gasoline", not "hybrid".
6. Field hygiene. model and trim under 25 characters each.
7. Sourcing. Downgrade any "high" confidence with no real source behind it. Delete any URL
   you cannot open.

Apply every correction you find, then return the corrected record plus the list of issues.
```

---

## Block D — cross-model comparison

Give this ONE agent the whole set of curves at once. This finds errors the per-car agents
cannot see, because each of them was isolated to a single car.

Format each row as:

```
<id> | <model> <trim> | <powertrain> | cost <real_cost> | retention 1y <%> 3y <%> 5y <%> 7y <%> 10y <%> | 10y maint <total>
```

```
Below are vehicles researched independently, so nobody has compared them against each other.
Retention is private-sale price as a percentage of the real purchase cost.

Find the records that are wrong RELATIVE TO THE OTHERS:
- Powertrain ordering. In Taiwan today: hybrid retains best, then gasoline, then PHEV, then
  BEV. A record breaking that order needs hard evidence.
- Trim ladder, when comparing trims of one model. The retention percentage should drift down
  as trims get pricier, but the ABSOLUTE resale price must still rise. A pricier trim that
  resells for less money is an error.
- Segment logic. SUVs and MPVs retain better than sedans of the same brand and price. Larger
  and more expensive models lose a higher percentage.
- Maintenance coherence. Same brand and powertrain should be similar, scaled by size and tire
  cost. A large SUV cheaper to maintain than a compact sedan is wrong. A BEV should be clearly
  cheaper than combustion models but never near zero.
- Suspiciously smooth curves. Even steps or round-numbered endings suggest invention rather
  than research.
- Outliers. Retention more than about 10 points from siblings without a stated reason.

Flag only records that genuinely need re-work. Be selective. For each, say precisely what to
re-check. Also summarise how these cars order on value retention.
```

---

## Workflow shape

```js
// Scout the real lineup first — never assume which models are on sale.
const scouted = await parallel(BRANDS.map(b => () => agent(scoutPrompt(b), {schema: SCOUT})))
const models = scouted.flatMap(s => s.models).filter(m => !EXISTING.includes(m.id))

// Research and verify each car independently. pipeline(), not parallel() — a car can start
// verification while another is still being researched.
const results = await pipeline(models, research, verify)

// Cross-check needs every curve at once, so it is a real barrier.
const flagged = await agent(crossCheckPrompt(results), {schema: CROSSCHECK})

// Repair only what was named.
await parallel(flagged.map(f => () => agent(repairPrompt(f))))
```

Have each verify agent write its final record to a file. Batches get interrupted — session
limits, stops — and a record on disk survives while a return value does not. Four batches ran
this way and one was interrupted; nothing was lost.

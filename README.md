# roll.py

A command line dice roller.

## Usage

    python roll.py <roll arg> <another roll arg> <and so on>
    
## Roll arguments

At its core, `roll.py` allows you to roll what you'd say: for example, 
`d4`, or `2d8`, or `10d6+15`. The dice are all rolled separately, then
summed, then the modifier is applied.

`roll.py` also supports rounding up (`^`) or down (`_`) for division 
modifiers: `3d6/2^` or `2d10/3_`.

Finally, you can label each roll:

    python roll.py attack:d20+5 defense:2d10+2 "power attack:1d8"

Your results will be returned in an ASCII table.

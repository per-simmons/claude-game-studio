# The Locked Study

*Fenwick Hall, Northumberland. 14 February 1951, 11:30 PM.*

Edmund Grale, collector of old maps, lies dead in his study. The door was bolted on the inside; his
housekeeper and his secretary had to break the frame to reach him. The river has flooded the lane, so
nobody has left the house. At two o'clock the coroner's van gets through and the county takes the
case. You have two and a half hours.

- **Suspects:** Iris Grale (the niece and heir), Tobias Wren (the secretary), Hester Moss (the housekeeper)
- **Your partner:** Constable June Pike, who knows the house. Talk to her when you're stuck.
- **Length:** about 10 minutes. Five endings.

## How to play (free, in your terminal)

```bash
python3 scripts/casepack/play.py examples/case-packs/the-locked-study
```

Type `help` once you're in. The basics: `look`, `examine <thing>`, `talk <name>`, then just type
questions in plain English. When someone's story doesn't add up, `present <card> to <claim>`. Read your
`notebook`, and `accuse` when you can prove where the killer really was, why they did it, and how.

Check the pack: `python3 scripts/casepack/lint.py examples/case-packs/the-locked-study`

`case-file.json` contains the solution. Don't open it before you play.

Licence: CC BY 4.0.

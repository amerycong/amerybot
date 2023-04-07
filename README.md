# amerybot

todo:
-validate match pulling
-finish moving all hardcoded variables/params to configs
-surely riot will reimplement by-tournament-code so i can stop my hacky way of filtering
-proper logging/debug
-more verbose help commands
-some case insensitive checking might be nice qol
-unsure how nicely IGNs with weird characters will be handled
-linting
-can't auto generate tourney codes since no production key (unless jankily automated via selenium/pyautogui+battlefy or something lol)
-inhouse functionality used to live in a colab notebook but has diverged for bot integration purposes. should eventually have a standalone inhouse (sub)module that's part of the bot
- +/- stats on inhouse output after each game (green/red arrows showing changes in stats from previous game)
-parallelize role permutation checks
-ability to recreate match history view from match data
-it worked at some point, but verify ability to backup game data jsons to google drive/cloud
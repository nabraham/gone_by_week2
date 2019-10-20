from typing import Dict, List, Tuple
import numpy
import os
import re
import argparse
from collections import defaultdict


def print_pick_set(pick_set, league_schedule) -> None:
    picks = pick_set[0]
    prob = pick_set[1]
    starting = len(picks) - len(league_schedule)
    print(''.join(['\n', str(int(prob * 10000) / 100), '\n-------']))
    for i, week in enumerate(league_schedule):
        week_pick = picks[i+starting]
        matchup = list(filter(lambda x: week_pick in x, week))[0]
        v = week_pick == matchup[0]
        h = week_pick == matchup[1]
        opn = ['', '[']
        cls = ['', ']']
        print(''.join([opn[v], matchup[0], cls[v],' @ ', opn[h], matchup[1], cls[h]]))


def best(pick_sets, n):
    pick_sets.sort(key=lambda x: x[1], reverse=True)
    return pick_sets[0:n]


def thresh(n):
    if n > 0.95:
        return 0.95
    elif n < 0.05:
        return 0.05
    else:
        return n

    
def clean(pick_sets):
    cleaned = {}
    for p in pick_sets:
        key = ''.join(p[0])
        if key not in cleaned or p[1] > cleaned[key][1]:
            cleaned[key] = p
    return list(cleaned.values())


def calculate_pick_sets(league_schedule: List[List[str]],
                        team_records: Dict[str, Tuple[float, float]],
                        selected_teams: List[str],
                        prune: bool) -> List[Tuple[List[str], float]]:
    queue = [(selected_teams, 1)]
    for i, week in enumerate(league_schedule):
        print('processing week', i, '(', len(queue), ')')
        new_queue = []
        for game in week:
            visitor = game[0]
            home = game[1]
            visitor_win = thresh(team_records[visitor][0] * 0.95)
            visitor_lose = thresh(team_records[visitor][1] * 1.05)
            home_win = thresh(team_records[home][0] * 1.05)
            home_lose = thresh(team_records[home][1] * 0.95)
            hv = home_win * visitor_lose
            vh = visitor_win * home_lose
            total = hv + vh
            composite_home = hv / total
            composite_visitor = vh / total
            for pick_set in queue:
                if visitor not in pick_set[0] and composite_visitor >= composite_home and composite_visitor > 0.75:
                    new_queue.append((pick_set[0] + [visitor], pick_set[1] * composite_visitor))
                if home not in pick_set[0] and composite_home >= composite_visitor and composite_home > 0.75:
                    new_queue.append((pick_set[0] + [home], pick_set[1] * composite_home))
        if len(new_queue) > 0:
            if prune:
                queue = clean(new_queue)
            else:
                queue = new_queue
        else:
            return queue
    return queue


def parse_schedule(filename: str, ending: int, starting: int) -> List[List[str]]:
    with open(filename) as f:
        by_team = list(map(lambda x: x.split('\t'), f.read().strip().split('\n')))
        weeks = numpy.array(by_team).transpose()
        root = weeks[0]
        week_dict = defaultdict(list)
        for i, week in enumerate(weeks[1:]):
            for j, team in enumerate(week):
                if team[0] == '@':
                    week_dict[i+1].append((root[j], week[j][1:]))
        return list(map(lambda x: week_dict[x], range(starting, ending+1)))


# 2018 sample score line
# 	CIN 34, IND 23	Andrew Luck 319	Joe Mixon 95	A.J. Green 92
# 2019 sample score line
# GB 10, CHI 3    Mitchell Trubisky 228    Aaron Jones 39    Allen Robinson II 102

score_pattern = re.compile('^\t?([A-Z]+) (\\d+), ([A-Z]+) (\\d+).*')


def parse_records(season_dir) -> Dict[str, Tuple[float, float]]:
    loss = 0
    win = 1
    team_records = defaultdict(list)
    for root, dirs, files in os.walk(season_dir):
        for file in files:
            with open('season/' + file) as f:
                lines = f.read().strip().split('\n')
                scores = filter(lambda x: score_pattern.match(x), lines)
                for line in scores:
                    match = score_pattern.match(line)
                    if int(match.group(2)) > int(match.group(4)):
                        team_records[match.group(1)].append(win)
                        team_records[match.group(3)].append(loss)
                    elif int(match.group(4)) > int(match.group(2)):
                        team_records[match.group(1)].append(loss)
                        team_records[match.group(3)].append(win)

    recs = {}
    for team in team_records:
        overall_winning_percentage = sum(team_records[team]) / len(team_records[team])
        recent_winning_percentage = sum(team_records[team][-2:]) / 2
        weighted_winning = 0.8 * overall_winning_percentage + 0.2 * recent_winning_percentage
        recs[team] = (weighted_winning, 1 - weighted_winning)

    return recs


def parse_chosen(filename: str) -> List[str]:
    with open(filename) as f:
        return list(f.read().strip().split('\n'))
        

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='make picks for survival football')
    parser.add_argument('--sw', dest='starting_week', type=int, default=1, help='starting week (default = 1)')
    parser.add_argument('--ew', dest='ending_week', type=int, default=17, help='ending week (default = 17)')
    parser.add_argument('--chosen', dest='chosen',  default='chosen.txt', help='file containing list of teams already picked / wish to save (default = chosen.txt)')
    parser.add_argument('--schedule', dest='schedule', default='schedule.txt', help='espn schedule as grid txt file (default = schedule.txt)')
    parser.add_argument('--season', dest='season', default='season', help='directory containing espn weekly scores [01.txt, 02.txt...] (default = season)')
    parser.add_argument('--prune', dest='prune', default=False, type=bool, help='prune the pick_set queue between weekly iterations (default = False)')
    parser.add_argument('--n', dest='n_best', default=10, type=int, help='number of pick_sets to show upon complettion (default = 10)')
    args = parser.parse_args()

    schedule = parse_schedule(args.schedule, args.ending_week, args.starting_week)
    records = parse_records(args.season)
    chosen = parse_chosen(args.chosen)

    all_picks = calculate_pick_sets(schedule, records, chosen, args.prune)
    list(map(lambda x: print_pick_set(x, schedule), best(all_picks, args.n_best)))

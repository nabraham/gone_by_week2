import numpy
import os
import re
import argparse
from collections import defaultdict

def print_pickset(pickset, schedule):
    picks = pickset[0]
    prob = pickset[1]
    starting = len(picks) - len(schedule)
    print(''.join(['\n', str(int(prob * 10000) / 100), '\n-------']))
    for i, week in enumerate(schedule):
        week_pick = picks[i+starting]
        matchup = list(filter(lambda x: week_pick in x, week))[0]
        v = week_pick == matchup[0]
        h = week_pick == matchup[1]
        opn = ['','[']
        cls = ['',']']
        print(''.join([opn[v], matchup[0], cls[v],' @ ', opn[h], matchup[1], cls[h]]))


def best(picksets, n):
    picksets.sort(key=lambda x: x[1], reverse=True)
    return picksets[0:n]


def thresh(n):
    if n > 0.95:
        return 0.95
    elif n < 0.05:
        return 0.05
    else:
        return n

    
def clean(picksets):
    cleaned = {}
    for p in picksets:
        key = ''.join(p[0])
        if key not in cleaned or p[1] > cleaned[key][1]:
            cleaned[key] = p
    return list(cleaned.values())


def main(schedule, records, chosen, prune, n_best):
    queue = [(chosen, 1)]
    for i, week in enumerate(schedule):
        print('processing week', i, '(', len(queue), ')')
        new_queue = []
        for game in week:
            visitor = game[0]
            home = game[1]
            v_win = thresh(records[visitor][0] * 0.95)
            v_lose = thresh(records[visitor][1] * 1.05)
            h_win = thresh(records[home][0] * 1.05)
            h_lose = thresh(records[home][1] * 0.95)
            hv = h_win * v_lose
            vh = v_win * h_lose
            T = hv + vh
            H = hv / T
            V = vh / T
            for pickset in queue:
                if visitor not in pickset[0] and V >= H:
                    new_queue.append((pickset[0] + [visitor], pickset[1] * V))
                if home not in pickset[0] and H >= V:
                    new_queue.append((pickset[0] + [home], pickset[1] * H))
        if len(new_queue) > 0:
            if prune:
                queue = clean(new_queue)
            else:
                queue = new_queue
        else:
            return best(queue, n_best)
    return best(queue, n_best)


def parse_schedule(filename, ending, starting):
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

# Sample score line
#	CIN 34, IND 23	Andrew Luck 319	Joe Mixon 95	A.J. Green 92	
score_pattern = re.compile('\t([A-Z]+) (\d+), ([A-Z]+) (\d+).*')
def parse_records(season_dir):
    LOSS = 0
    WIN = 1
    records = defaultdict(list)
    for root, dirs, files in os.walk(season_dir):
        for file in files:
            with open('season/' + file) as f:
                lines = f.read().strip().split('\n')
                scores = filter(lambda x: x.startswith('\t'), lines)
                for line in scores:
                    match = score_pattern.match(line)
                    if int(match.group(2)) > int(match.group(4)):
                        records[match.group(1)].append(WIN)
                        records[match.group(3)].append(LOSS)
                    elif int(match.group(4)) > int(match.group(2)):
                        records[match.group(1)].append(LOSS)
                        records[match.group(3)].append(WIN)

    recs = {}
    for team in records:
        winning_pctg = sum(records[team]) / len(records[team])
        recent_pctg = sum(records[team][-2:]) / 2
        winning = 0.8 * winning_pctg + 0.2 * recent_pctg
        recs[team] = (winning, 1-winning)

    return recs


def parse_chosen(filename):
    with open(filename) as f:
        return list(f.read().strip().split('\n'))
        

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='make picks for survival football')
    parser.add_argument('--sw', dest='starting_week', type=int, default=1, help='starting week (default = 1)')
    parser.add_argument('--ew', dest='ending_week', type=int, default=17, help='ending week (default = 17)')
    parser.add_argument('--chosen', dest='chosen',  default='chosen.txt', help='file containing list of teams already picked / wish to save (default = chosen.txt)')
    parser.add_argument('--schedule', dest='schedule', default='schedule.txt', help='espn schedule as grid txt file (default = schedule.txt)')
    parser.add_argument('--season', dest='season', default='season', help='directory containing espn weekly scores [01.txt, 02.txt...] (default = season)')
    parser.add_argument('--prune', dest='prune', default=False, type=bool, help='prune the pickset queue between weekly iterations (default = False)')
    parser.add_argument('--n', dest='n_best', default=10, type=int, help='number of picksets to show upon complettion (default = 10)')
    args = parser.parse_args();

    schedule = parse_schedule(args.schedule, args.ending_week, args.starting_week)
    records = parse_records(args.season)
    chosen = parse_chosen(args.chosen)

    picks = main(schedule, records, chosen, args.prune, args.n_best)
    list(map(lambda x: print_pickset(x, schedule), picks))

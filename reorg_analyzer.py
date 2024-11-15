# Example command: 
#  python reorg_analyzer.py bsc.log 
import re
from collections import defaultdict

def parse_logs(log_file_path):
    # Regular expressions to match log lines
    re_import = re.compile(
        r't=.* lvl=info msg="Imported new chain segment" number=(\d+) '
        r'hash=([0-9a-fx]+) miner=([0-9a-zA-Zx]+)'
    )
    re_reorg = re.compile(
        r't=.* lvl=info msg="Chain reorg detected" number=(\d+) hash=([0-9a-fx]+) '
        r'drop=(\d+) dropfrom=([0-9a-fx]+) add=(\d+) addfrom=([0-9a-fx]+)'
    )

    # Dictionaries to store block information
    block_info = {}
    reorgs = []

    with open(log_file_path, 'r') as f:
        for line in f:
            # Check for imported block lines
            match_import = re_import.search(line)
            if match_import:
                block_number = int(match_import.group(1))
                block_hash = match_import.group(2)
                miner = match_import.group(3)
                block_info[block_hash] = {
                    'number': block_number,
                    'miner': miner
                }
                continue

            # Check for reorg lines
            match_reorg = re_reorg.search(line)
            if match_reorg:
                reorg_number = int(match_reorg.group(1))
                reorg_hash = match_reorg.group(2)
                drop_count = int(match_reorg.group(3))
                drop_from_hash = match_reorg.group(4)
                add_count = int(match_reorg.group(5))
                add_from_hash = match_reorg.group(6)
                reorgs.append({
                    'number': reorg_number,
                    'hash': reorg_hash,
                    'drop_count': drop_count,
                    'drop_from_hash': drop_from_hash,
                    'add_count': add_count,
                    'add_from_hash': add_from_hash
                })

    return block_info, reorgs

def analyze_reorgs(block_info, reorgs):
    results = []
    validator_reorgs = defaultdict(lambda: {'count': 0, 'blocks': []})

    for reorg in reorgs:
        # Get the dropped and added block hashes
        dropped_hash = reorg['drop_from_hash']
        added_hash = reorg['add_from_hash']

        # Get miner information
        dropped_miner = block_info.get(dropped_hash, {}).get('miner', 'Unknown')
        added_miner = block_info.get(added_hash, {}).get('miner', 'Unknown')

        # Construct the result
        result = {
            'reorg_at_block': reorg['number'],
            'dropped_block_hash': dropped_hash,
            'added_block_hash': added_hash,
            'dropped_miner': dropped_miner,
            'added_miner': added_miner,
            'responsible_validator': added_miner
        }
        results.append(result)

        # Update the validator reorgs data
        validator = added_miner
        validator_reorgs[validator]['count'] += 1
        validator_reorgs[validator]['blocks'].append(reorg['number'])

    return results, validator_reorgs

def main():
    import argparse

    parser = argparse.ArgumentParser(description='Analyze BSC node logs for reorgs.')
    parser.add_argument('logfile', help='Path to the log file to analyze.')
    args = parser.parse_args()

    block_info, reorgs = parse_logs(args.logfile)
    results, validator_reorgs = analyze_reorgs(block_info, reorgs)

    # Print the detailed reorg results
    for res in results:
        print(f"Reorg detected at block number {res['reorg_at_block']}:")
        print(f"  Dropped block hash: {res['dropped_block_hash']}")
        print(f"  Dropped miner: {res['dropped_miner']}")
        print(f"  Added block hash: {res['added_block_hash']}")
        print(f"  Added miner: {res['added_miner']}")
        print(f"  Validator responsible for reorg: {res['responsible_validator']}")
        print('-' * 60)

    # Print the aggregated summary
    print("\nAggregated Validators Responsible for Reorgs:\n")
    print(f"{'Validator Address':<46} {'Number of Reorgs':<16} {'Block Numbers'}")
    print('-' * 90)
    for validator, data in sorted(validator_reorgs.items(), key=lambda x: x[1]['count'], reverse=True):
        block_numbers = ', '.join(map(str, data['blocks']))
        print(f"{validator:<46} {data['count']:<16} {block_numbers}")

if __name__ == '__main__':
    main()

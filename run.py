from htras import simulator, database
import argparse
    
def migrate():
    print('Migrating database...')
    database.drop_table(['ledger', 'customers'])
    database.create_table('ledger', [
        'idx UInt32 NOT NULL', 'cid UInt32 NOT NULL', 
        'hash String', 'data String', 'prev String', 'sig String',
        'PRIMARY KEY idx'
    ])

def init(args):
    if args.refresh:
        migrate()
        
    simulator.simulate(args.env)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-e', '--env', type=str, help='/path/to/env', required=True)
    parser.add_argument('-r', '--refresh', action='store_true', help='Refresh database migration')
    args = parser.parse_args()
    
    init(args)
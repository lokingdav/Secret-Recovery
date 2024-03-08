from skrecovery import database
    
def migrate():
    print('Migrating database...')
    database.drop_table(['pending_txs' 'ledgers'])
    
    database.create_table('ledgers', [
        '`id` INT AUTO_INCREMENT PRIMARY KEY',
        "`chainid` VARCHAR(255) NOT NULL",
        '`header` JSON',
        '`data` JSON',
        '`metadata` JSON'
    ])
    
    database.create_table('pending_txs', [
        'id INT AUTO_INCREMENT PRIMARY KEY', 
        'payload JSON', 
        'created_at TIMESTAMP'
    ])

if __name__ == "__main__":
    migrate()
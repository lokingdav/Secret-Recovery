from skrecovery import database
    
def migrate():
    print('Migrating database...')
    database.drop_table(['posted_txs', 'pending_txs', 'ledgers'])
    
    database.create_table('ledgers', [
        '`id` INT AUTO_INCREMENT PRIMARY KEY',
        "`chainid` VARCHAR(255) NOT NULL",
        '`header` LONGTEXT NOT NULL',
        '`data` LONGTEXT NOT NULL',
        '`metadata` LONGTEXT NOT NULL'
    ])
    
    database.create_table('pending_txs', [
        'id INT AUTO_INCREMENT PRIMARY KEY', 
        'payload LONGTEXT NOT NULL', 
        'created_at TIMESTAMP'
    ])
    
    database.create_table('posted_txs', [
        'id INT AUTO_INCREMENT PRIMARY KEY', 
        'txid VARCHAR(255) NOT NULL',
        'block_id INT NOT NULL', 
        'created_at TIMESTAMP',
        'INDEX `txid` (`txid`)',
    ])

if __name__ == "__main__":
    migrate()
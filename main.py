import acessoBanco 

userDB = 'elysia'
passDB = '96by&cN43dgVC^b-9MsN'
nameDB = 'elysiaDB'
serverName = 'datasheets.cipnvcm3pv2h.us-east-1.rds.amazonaws.com,9856'

acessoBanco.conexaoBanco(server=serverName, user=userDB, password=passDB, dataBase=nameDB)
b = requests.basic('https://elysia.zeev.it/api/2/docs', headers={'Authorization': 'Bearer 3Lzf1s6YuSVLM%2Bz%2FxAEaXUgeiX8UZUW4TpQz8Dkf9KQDX4yLt5mN997v9KtsYbua'})
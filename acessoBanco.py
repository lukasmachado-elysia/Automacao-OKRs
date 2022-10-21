from ast import Str
from sqlite3 import Cursor
import pyodbc

# faz a conexao com o SQL Server e consulta a um banco de dados 
def conexaoBanco(server=Str,
                    user=str, 
                    password=str, 
                    dataBase=str):
    '''
        Funcao que faz conexao com o banco de dados. 
        Retorna a conexao com o banco.

        Parametros
        ----------

        server : string
            endereco do servidor
        user : string
            nome do usuario para conexao
        password: string
            senha do usuario para conexao
        database: string
            nome do banco que deseja realizar a conexao



        Exemplo de uso
        --------------

            * pegando acesso do banco \n
                conn = acessoBanco.conexaoBanco(server=serverName, user=userDB, password=passDB, dataBase=nameDB)
            \n
            * pegando o nome de todos os 'colaboradores' \n
                cursor = conn.cursor()
                cursor.execute("select * from vendedores;")
                column = cursor.fetchone()
            \n
            * printando nome de todos \n
                while column:
                    print(column[1])
                    column = cursor.fetchone()

        Retorno
        -------
            obj : type connection.
                Retorna a conexao com o banco.

    '''
    instancia = 'DRIVER={ODBC Driver 18 for SQL Server};' +'SERVER=' + server + ';' + 'DATABASE=' + dataBase + ';' + 'TrustServerCertificate=YES;' +  'UID=' + user + ';' + 'PWD=' + password + ';'
    
    #print(f'Instancia de conexao: {instancia}')
    try:
        conn = pyodbc.connect(instancia)
        print('\n------------------------------------') 
        print(' Conexao estabelecida com sucesso!')
        print('------------------------------------\n') 
        return conn
    except Exception as e:
        print('\n------------------------------------') 
        print('Nao foi possível realizar a conexao!')
        print('------------------------------------\n') 

        templateError = '!!! ---> Um erro do tipo: "{0}" ocorreu <--- !!!\nArgumentos:\n{1}'
        messageError = templateError.format(type(e).__name__,e.args)
        print(messageError)

        return messageError
    
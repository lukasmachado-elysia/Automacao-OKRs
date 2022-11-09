import pandas as pd
import time
import numpy as np
import funcoes
from datetime import datetime, timedelta
from dateutil import parser
from flask import Flask, render_template
from flask_mail import Mail, Message
import os

# Variaveis globais
tks = ['HihrPwM6iplpMc20YafyI0X20hYBwMJjn9O5b3uRXLc%3D','NHvW6AeyLM3HFKp1HwXQIbDbGVdDOyMhvbyHgEoZY57S4pEFqdDDKy1R%2FVQHplHm','UVzI3W1fv8mAK28sWaTc%2BOlAefhF1q26WWTfaOmb%2BSY6F1b2IE43cgRMrafYMySh','oAlfna7l2QNiS6nZo4oIQSQCpNo5XX9iydYqEGfMVkDVz8fBG2Vl6bW9lChTtGtP', 'vcMSbDWqyMNu8fcVLol8l0dZ0DZhinIFKyydHCBSAb%2B5RloWjteXNY9345MIcbUQ']
metodo = 'GET'
url = "https://elysia.zeev.it"
tipoUrl = "/api/2/assignments"
filtro = {'flowId': 0}

# Datas
today = datetime.today().strftime('%Y-%m-%d')
periodo1 = (datetime.today() - timedelta(days=7)).strftime('%Y-%m-%d')
periodo2 = today

# Se a API alterar seu campos novamente, sera necessario alterar apenas alguns filtros desta funcao
def request_Orquestra(method='GET',urlReq="https://elysia.zeev.it",typeReq="/api/2/assignments",tokens={},filters={}, forceRequisition:bool=False) -> list:
        try:
                # Variaveis de controle
                row = 1
                i = 1
                retorno = []
                # filtros base para o payload
                if not typeReq.lower().__contains__('report'):
                        filters['recordsPerPage'] = 100
                        seconds = 1
                else:
                        if not forceRequisition: 
                                print("---- >> Requisicao lenta... << ---- ")
                                filters['recordsPerPage'] = 30
                                seconds = 3
                        else:
                                print("---- >> Requisicao forçada... << ---- ")
                                filters['recordsPerPage'] = 100
                                seconds = 1    
                
                filters['mobileEnabledOnly'] = False
                # Faz a busca para cada token
                for tk in tokens:
                        # Reseta variaveis de controle
                        row = 1
                        i = 1
                        # Iteracao com token
                        authorization= {'Authorization': "Bearer " + tk}
                        while row != 0:
                                # Aguardo x segundos devido ao limite de requisicoes - lembrando que a limite de requisicoes por segundos, minutos, horas, dias e meses
                                time.sleep(seconds) 
                                
                                # Incremento de pagina
                                filters['pageNumber'] = i
                                
                                # Requisicao
                                getReq = funcoes.requests_API_Orquestra(metodo=method, 
                                                                        urlAcesso=urlReq, 
                                                                        tipoAcesso=typeReq, 
                                                                        head=authorization, 
                                                                        payload=filters)
                                
                                # Resultado JSON da requisicao
                                result = getReq.json()
                                        
                                # Checa se esta vazio o resultado, o que significa que nao tem mais paginas
                                if (len(result) == 0) or (getReq.status_code != 200):
                                        break
                                else:
                                        # coloca cada retorno na lista
                                        retorno.append(result)
                                        i+=1
                # Cada usuario do token fica em uma sublista da lista de retorno, por isto a necessidade de 'explodir' ela dentro de outra lista.
                retornoLista = [item for sublista in retorno for item in sublista]
                return retornoLista 
        except Exception as e:
                funcoes.printError(e)
                return []

def formata_DataFrame(lista:list):
    '''
        Funcao
        ------
            Faz a formatacao do data frame colocando as no formato correto e criando uma coluna chamada `atrasada`.

        Parametros
        ----------
            lista: list (obrigatorio)
                Lista com dicionario JSON, para formatacao em data frame.
        
        Retorno
        -------
            Retorna o dicionario em um formato de `DataFrame`.
            * Se erro, retorna -1. 
    '''
    # verifica se houve retorno
    try:
        # ocorreu erro ou nao ocorreram retornos - provisorio
        if len(lista) <= 0:
            df = pd.DataFrame
            return df
        # houve retorno de linhas
        elif len(lista) > 0:
            df = pd.DataFrame(lista)
            # Colocando o idTask para conferencia
            df['idTask'] = pd.DataFrame(df['instance'].apply(pd.Series))['id']
            # selecionando apenas as colunas necessarias
            df = df[['idTask','id','taskName','requestName','startDateTime','expirationDateTime','flow','instance']]

            # convertendo colunas para datetime
            df['expirationDateTime'] = pd.to_datetime(df['expirationDateTime'])
            df['startDateTime'] = pd.to_datetime(df['startDateTime'])

            # formatando data em DD/MM/YY
            df.loc[:,'expirationDateTime'] = df.loc[:,'expirationDateTime'].dt.strftime('%Y-%m-%d')
            df.loc[:,'startDateTime'] = df.loc[:,'startDateTime'].dt.strftime('%Y-%m-%d')

            # convertendo colunas para datetime
            df['expirationDateTime'] = pd.to_datetime(df['expirationDateTime'])
            df['startDateTime'] = pd.to_datetime(df['startDateTime'])

            # adiciona coluna de tarefa atrasada
            df['taskAtrasada'] = False
            df.loc[today > df['expirationDateTime'],['taskAtrasada']] = True
            
            return df
    except Exception as e:
        print('--> Erro na funcao \'contagem_CS1\' <--')
        funcoes.printError(e)
        return -1

def contagem_Instancias_Orquestra(nomeSolicitacao:str, nomeTarefa:str,per1:datetime,per2:datetime,dataFrame:pd.DataFrame, status:str='endDateTime') -> int:
    '''
     Funcao
     ------
            Retorna a contagem de tarefas fechadas ou abertas para determinada solicitacao em um determinado periodo.

    Parameters
    ----------
        nomeSolicitacao: str (obrigatorio)
            Nome da solicitacao que sera buscada e contada a instancia.
        
        nomeTarefa: str (obrigatorio)
            Nome da tarefa para ser contada a sua quantidade.

        dataFrame: dataFrame Pandas (obrigatorio)
            Dataframe que sera utilizado como base de dados para a contagem.
        
        per1: datetime (obrigatorio)
            Periodo inicial para busca.

        per2: datetime (obrigatorio)
            Periodo final para busca.

        status: str (opcional)
            Status da data para verificar o periodo - podendo ser `endDateTime` ou `startDateTime`.
    Retorno
    -------
        Retorna a quantidade de instancias em `int` ja finalizadas desta tarefa.
        * Se erro, retorna -1   
    '''
    try:
        # Formatar parametros - remove espacos em branco, deixar em letra minuscula
        nomeSolicitacao = str(nomeSolicitacao).lower().replace(" ","")
        nomeTarefa = str(nomeTarefa).lower()
        # Projetos 
        projetos = dataFrame.loc[(dataFrame['requestName'].str.lower().str.replace(" ","").str.contains(nomeSolicitacao))]
        # Contagem
        cont=0
        # Percorre linha a linha do dataframe, verificando cada instancia aberta ou fechada da solicitacao 
        for row in projetos.values:
            for instance in row[19]:
                task = str(instance['task']['name']) 
                date = parser.parse(instance[status]).strftime("%Y-%m-%d")
                if task.lower().__contains__(nomeTarefa):
                    if date >= per1 and date <= per2:
                        cont+=1
                        break
        return cont
    except Exception as e:
        print('--> Erro na funcao \'contagem_Instancias_Orquestra\' <--')
        funcoes.printError(e)
        return -1

def instances_Report_Orquestra(userToken:str, showFinishedTasks:bool=True, activeInstances:bool=True, flowId:str=''):
    '''
        Funcao
        ------
            Lista todas instâncias de solicitações que a pessoa relacionada ao token possui permissão de consultar de acordo com filtros.
        
        Parametros
        ----------
            userToken: str (obrigatorio)
                Token do usuario orquestra para solicitar a requisicao.

            showFinishedTasks: boolean (opcional)
                Definir se vai filtrar por instancias fechadas ou instancias abertas das solicitacoes.
            
            activeInstances: boolean (opcional)
                Definir se a solicitacao esta `Finalizada` ou `Em andamento`.

            flowId: str (opcional)
                Filtrar pelo id de instancia.
        Retorno 
        -------
            Retorna um `DataFrame`.
            * Se erro, retorna -1.
    '''
    try:
        # Filtro padrao - Solicitacoes Em andamento e com instancias Finalizadas
        f = {"startDateIntervalBegin": "2000-01-01T00:00:00",
                "startDateIntervalEnd": "2030-12-31T23:59:59",
                "showFinishedInstanceTasks": True, 
                "showPendingInstanceTasks": False,
                "active": activeInstances}

        # Escolhe se vai mostrar solicitacoes Finalizadas ou Em andamento
        if not activeInstances:
            # Vai mostrar solicitacoes Finalizadas
            f['showFinishedInstanceTasks'] = False
            f['showPendingInstanceTasks'] = False
        else:
            # Vai mostrar solicitacoes Em andamento e com instancias Pendentes
            if showFinishedTasks == False: 
                f['showFinishedInstanceTasks'] = False
                f['showPendingInstanceTasks'] = True

        # Filtro de ID para solicitacoes especificas
        if flowId != '': 
            f['flowId'] = flowId
        # Requisicao 
        lista = request_Orquestra(method='GET',
                                    urlReq=url,
                                    typeReq='/api/2/instances/report',
                                    tokens=[userToken],
                                    filters=f,
                                    forceRequisition=(not activeInstances)) # Requisicao forcada no caso de solicitacoes Finalizadas
        df = pd.DataFrame(lista)
        return df
    except Exception as e:
        print('--> Erro na funcao \'instances_Report_Orquestra\' <--')
        funcoes.printError(e)
        return -1

def envia_Email(enderecosEnvio:list, assunto:str, mensagem:str, listAttach:list=[]) -> str:
    '''
        Funcao
        ------

            Envia e-mail para os enderecos de envio especificados na lista.
            * O e-mail `bot.elysia@gmail.com` e o remetente.
    
        Parametros
        ----------
            enderecosEnvio : list, obrigatorio
                Uma lista dos enderecos de e-mail que receberao o e-mail.
            
            assunto : str, obrigatorio
                O assunto que ira no e-mail.
            
            mensagem : str, obrigatorio
                A mensagem que sera colocada no corpo do e-mail.
            
            listAttach : list, opcional
                Uma lista composta por uma sublista com: `[ ["caminhoAnexo", "nomeAnexo", "tipoAnexo"] ]`.\n 
                Para o `tipoAnexo`, verificar documentacao do FLASK.
                
        Retorno
        -------
            Retorna uma `string` especificando se o envio foi realizado com sucesso ou nao.
    '''
    try:
        # Dados do email e flask
        password = 'xeppbwvbemvrpgms'
        app  = Flask(__name__)
        mail = Mail(app)
        
        print(">> Funcao de envio automatico de e-mail v1.0 <<\n")
        print(">> Conectando ao servidor do Gmail...")

        # Configurando conexao com servidor de e-mail
        app.config['MAIL_SERVER'] = 'smtp.gmail.com'
        app.config['MAIL_PORT'] = 465
        app.config['MAIL_USERNAME'] = 'bot.elysia@gmail.com'
        app.config['MAIL_PASSWORD'] = password
        app.config['MAIL_USE_TLS'] = False
        app.config['MAIL_USE_SSL'] = True
        mail = Mail(app)

        print(">> Conectado com sucesso!")
        print(">> Montando e-mail...")

        with app.app_context():
            msg = Message(subject=assunto, sender=("Elysia Chlorotica Bot", "bot.elysia@gmail.com"), recipients=enderecosEnvio)
            #msg.body = mensagem
            msg.html = render_template("templateBotElysia.html",data=mensagem)
            # Se for para enviar com attachment
            if len(listAttach) == 0:
                print(">> Sem anexo para envio...")
            else:
                print(">> Anexando documentos...")
                for vals in listAttach:
                    with app.open_resource(vals[0] + vals[1]) as fp:
                        msg.attach(vals[1], vals[2], fp.read())
            print(">> Enviando e-mail...")
            mail.send(msg)
        return ">> E-mail enviado com sucesso para (" + ", ".join(enderecosEnvio) + ") no dia {0}!".format(datetime.today().strftime("%d/%m/%Y as %Hh:%Mm:%Ss"))
    except Exception as e:
        funcoes.printError(e)
        return ">> Nao foi possivel enviar o email!"


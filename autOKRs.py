import pandas as pd
import time
import funcoes
from datetime import datetime, timedelta
from dateutil import parser
import os

funcoes.cria_log("Automacao OKRs v1.0","autOKRs")

# Variaveis globais
tks = ["HihrPwM6iplpMc20YafyI0X20hYBwMJjn9O5b3uRXLc%3D","NHvW6AeyLM3HFKp1HwXQIbDbGVdDOyMhvbyHgEoZY57S4pEFqdDDKy1R%2FVQHplHm","UVzI3W1fv8mAK28sWaTc%2BOlAefhF1q26WWTfaOmb%2BSY6F1b2IE43cgRMrafYMySh","oAlfna7l2QNiS6nZo4oIQSQCpNo5XX9iydYqEGfMVkDVz8fBG2Vl6bW9lChTtGtP", "vcMSbDWqyMNu8fcVLol8l0dZ0DZhinIFKyydHCBSAb%2B5RloWjteXNY9345MIcbUQ"]
metodo = "GET"
url = "https://elysia.zeev.it"
tipoUrl = "/api/2/assignments"

# Log
funcoes.cria_log("Iniciando variaveis globais...","autOKRs")

# Tempo de exec programa
timeStart = time.process_time()

# Datas
today = datetime.today().strftime("%Y-%m-%d")
periodo1 = (datetime.today() - timedelta(days=7)).strftime('%Y-%m-%d')
periodo2 = today

funcoes.cria_log("Definindo periodo: {0} e {1}".format(periodo1, periodo2),"autOKRs")

# Se a API alterar seu campos novamente, sera necessario alterar apenas alguns filtros desta funcao
def request_Orquestra(method='GET',urlReq="https://elysia.zeev.it",typeReq="/api/2/assignments",tokens={},filters={}, forceRequisition:bool=False) -> list:
        try:
                # Variaveis de controle
                row = 1
                i = 1
                retorno = []
                # filtros base para o payload
                funcoes.cria_log("Requisicao para {}...".format(urlReq+typeReq),"autOKRs")
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
                funcoes.cria_log("Retornando resultados da requisicao...","autOKRs")
                retornoLista = [item for sublista in retorno for item in sublista]
                return retornoLista 
        except Exception as e:
                print('--> Erro na funcao \'request_Orquestra\' <--')
                funcoes.printError(e,"autOKRs")
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
    funcoes.cria_log("Formatando dataframe...","autOKRs")
    # verifica se houve retorno
    try:
        # ocorreu erro ou nao ocorreram retornos - provisorio
        if len(lista) <= 0:
            df = pd.DataFrame()
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
            funcoes.cria_log("Formatacao concluida com sucesso...","autOKRs")
            return df
    except Exception as e:
        print('--> Erro na funcao \'contagem_CS1\' <--')
        funcoes.printError(e,'autOKRs')
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
        int: Retorna a quantidade de instancias ja finalizadas desta tarefa.
        * Se erro, retorna -1   
    '''
    try:
        funcoes.cria_log("Realizando contagem de instancias...","autOKRs")
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
        funcoes.cria_log("Contagem de instancias concluida...","autOKRs")
        return cont
    except Exception as e:
        print('--> Erro na funcao \'contagem_Instancias_Orquestra\' <--')
        funcoes.printError(e,"autOKRs")
        return -1

def instances_Report_Orquestra(userToken:str, showFinishedInstanceTasks:bool=True, showPendingInstanceTasks:bool=False, activeInstances:bool=True, forceReq:bool=False, flowId:str=''):
    '''
        Funcao
        ------
            Lista todas instâncias de solicitações que a pessoa relacionada ao token possui permissão de consultar de acordo com filtros.
        
        Parametros
        ----------
            userToken : str, (obrigatorio)
                Token do usuario orquestra para solicitar a requisicao.
            
            Parametros de especial atencao:
            -------------------------------

            `showFinishedTasks` : boolean, (opcional)
                Define se vai requisitar instancias fechadas das solicitacoes.
            
            `showPendingInstanceTasks` : boolean, (opcional)
                Define se vai requisitar instancias abertas das solicitacoes.

            * Se nao optar por `showPendingInstanceTasks` ou `showFinishedTasks`, sera necessario colocar o parametro `forceReq` como `True`.\n
            * Se `showPendingInstanceTasks` ou `showFinishedTasks` estiverem `True` o parametro `forceReq` eh alterado para `False`, mesmo se ele for passado pela funcao.
            
            forceReq : boolean, (opcional)
                Este parametro limita a quantidade de solicitacoes por segundo.

            activeInstances : boolean, (opcional)
                Definir se a solicitacao esta `Finalizada` ou `Em andamento`.

            flowId : str, (opcional)
                Filtrar pelo id de instancia.
        Retorno 
        -------
            Retorna um DataFrame(Pandas).
            * Se erro, retorna -1.
    '''
    try:
        funcoes.cria_log("Realizando requisicao de instancias...","autOKRs")
        # Filtro padrao - Solicitacoes Em andamento e com instancias Finalizadas
        f = {"startDateIntervalBegin": "2000-01-01T00:00:00",
                "startDateIntervalEnd": "2030-12-31T23:59:59",
                "showFinishedInstanceTasks": showFinishedInstanceTasks, 
                "showPendingInstanceTasks": showPendingInstanceTasks,
                "active": activeInstances}
                
        # Filtro de ID para solicitacoes especificas
        if flowId != '': 
            f['flowId'] = flowId

        if showFinishedInstanceTasks == True | showPendingInstanceTasks == True:
            forceReq = False

        # Requisicao 
        lista = request_Orquestra(method='GET',
                                    urlReq=url,
                                    typeReq='/api/2/instances/report',
                                    tokens=[userToken],
                                    filters=f,
                                    forceRequisition=forceReq)
        funcoes.cria_log("Requisicao concluida...","autOKRs")
        df = pd.DataFrame(lista)
        return df
    except Exception as e:
        print('--> Erro na funcao \'instances_Report_Orquestra\' <--')
        funcoes.printError(e,"autOKRs")
        return pd.DataFrame()
def contagem_CS1(dataFrame:pd.DataFrame) -> list:
    '''
        Funcao
        ------
            Faz a contagem de clientes no fluxo CS1.

        Parametros
        ----------
            dataFrame: DataFrame (obrigatorio)
                Dataframe a ser utilizado na contagem.
        
        Retorno
        -------
            Retorna uma lista com os 3 valores de contagem para CS1: `[contCs1Abertos,contCs1Efetivos,contCS1Atrasadas]`.
            * Se erro, retorna uma lista contendo o valor `-1`.
    '''
    try:
        funcoes.cria_log("Realizando contagem CS1...","autOKRs")
        # CS1 Abertos sao os Efetivos Em espera + Em Aberto nas atribuicoes de cada usuario -> Pegar o relogio de 7/15 dias
        df = dataFrame
        cs1 = df.loc[(df['requestName'].str.lower().str.replace(" ","").str.contains('projetov.20')) & ((df['taskName'].str.lower().str.contains('ligação do cs')) | (df['taskName'].str.lower().str.replace(" ","").str.contains('cooldown')))]
        contCs1Abertos = len(cs1)

        # CS1 Efetivos sao os Em espera do 'Servico Orquestra'
        # Entrou no relogio de 7 ou 15 dias na semana do script, conta como efetivo
        cs1Efetivos = df.loc[(df['requestName'].str.lower().str.replace(" ","").str.contains('projetov.20')) 
                            & (df['taskName'].str.lower().str.replace(" ","").str.contains('cooldown'))
                            & (df['startDateTime'].between(periodo1,periodo2, inclusive='both'))]
        contCs1Efetivos = len(cs1Efetivos)

        # CS1 Atrasados 
        contCS1Atrasadas = len(cs1.loc[(df['taskAtrasada'] == True) & (df['taskName'].str.lower().str.contains('ligação do cs'))])
        funcoes.cria_log("Contagem CS1 concluida com sucesso...","autOKRs")
        return [contCs1Abertos,contCs1Efetivos,contCS1Atrasadas]
    except Exception as e:
        print('--> Erro na funcao \'contagem_CS1\' <--')
        funcoes.printError(e,"autOKRs")
        return [-1,-1,-1]

def contagem_CS2_Abertos_Degustacao(instancesDataFrame:pd.DataFrame) -> int:
    try:
        # Formatar parametros - remove espacos em branco, deixar em letra minuscula
        nomeSolicitacao = str('degustação').lower().replace(" ","")
        nomeTarefa = str('ligação do cs').lower()
        # Projetos 
        projetos = instancesDataFrame.loc[(instancesDataFrame['requestName'].str.lower().str.replace(" ","").str.contains(nomeSolicitacao))]
        # Contagem
        cont=0
        abertos=0
        for row in projetos.values:
            for instance in row[19]:
                task = str(instance['task']['name']) 
                if task.lower().__contains__(nomeTarefa):
                    cont+=1
                    break
            if cont>=1:
                abertos+=1 # conta a quantidade de abertos em degustacao
                cont=0
        return [abertos]
    except Exception as e:
        print('--> Erro na funcao \'contagem_CS2_Degustacao\' <--')
        funcoes.printError(e,"autOKRs")
        return [-1]

def contagem_CS2(dataFrame:pd.DataFrame, instancesDataFrame:pd.DataFrame, instancesCloseDataFrame:pd.DataFrame) -> list:
    '''
        Funcao
        ------
            Faz a contagem de clientes no fluxo CS2.
        
        Paramentros
        -----------
            dataFrame: DataFrame (obrigatorio)
                DataFrame utilizado para a contagem.
            
            instancesDataFrame: DataFrame (obrigatorio)
                DataFrame utilizado para a contagem.
        
        Retorno
        -------
            Retorna uma lista com os 3 valores de contagem para o CS2: `[contCs2Abertos,contCs2Efetivos,contCs2Atrasados]`
            * Se erro, retorna uma lista contendo o valor `-1`.
    '''
    try:
        funcoes.cria_log("Realizando contagem CS2...","autOKRs")
        df = dataFrame
        # CS2 Em aberto -> Para degustacao a etapa 'Inicio do mes seguinte' contabiliza os em aberto apos email = acomp personalizado 1/3
        cs2 = df.loc[(df['requestName'].str.lower().str.contains('degustação')) | (df['requestName'].str.lower().str.contains('normal')) & ~(df['taskName'].str.lower().str.contains('relatório')) | (df['taskName'].str.lower().str.contains('suporte'))]
        cs2Degustacao = contagem_CS2_Abertos_Degustacao(instancesDataFrame)[0]
        cs2Normal = contagem_fluxo_personalizado(instancesDataFrame)[0]
        contCs2Abertos =  cs2Degustacao + cs2Normal
        
        # CS2 Efetivos -> Em degustacao 
        cs2NormalInstancias = instancesDataFrame.loc[instancesDataFrame['requestName'].str.lower().str.contains('normal')] 
        cs2DegustacaoEfetivo = contagem_Instancias_Orquestra('degustação', 'ligação do cs', periodo1, periodo2, instancesDataFrame) + contagem_Instancias_Orquestra('degustação', 'ligação do cs', periodo1, periodo2, instancesCloseDataFrame)
        cs2NormalEfetivo = contagem_Instancias_Orquestra('normal', 'ligação do cs', periodo1, periodo2, cs2NormalInstancias) 
        contCs2Efetivos =  cs2DegustacaoEfetivo + cs2NormalEfetivo
        
        # CS2 Atrasados
        cs2Atrasados = cs2.loc[(cs2['taskName'].str.lower().str.contains('ligação do cs')) & (cs2['taskAtrasada'] == True)]
        contCs2Atrasados = len(cs2Atrasados)
        funcoes.cria_log("Contagem CS2 concluida com sucesso...","autOKRs")
        return [contCs2Abertos,contCs2Efetivos,contCs2Atrasados]
    except Exception as e:
        print('--> Erro na funcao \'contagem_CS2\' <--')
        funcoes.printError(e,"autOKRs")
        return [-1]

def contagem_fluxo_personalizado(instancesDataFrame:pd.DataFrame) -> list:
    '''
        Funcao
        ------
           Faz a contagem de clientes no fluxo personalizado.
        
        Parametros
        ----------
            instancesDataFrame: DataFrame (obrigatorio)
                DataFrame utilizado para contagem.
        
        Retorno
        -------
            Retorna uma lista contendo a quantidade de clientes para o fluxo personalizado: `[contClientesfluxoNormal]`
            * Se erro, retorna uma lista contendo o valor `-1`.
    '''
    try:
        funcoes.cria_log("Realizando contagem fluxo personalizado...","autOKRs")
        df = instancesDataFrame
        contClientesfluxoNormal = len(df.loc[df['requestName'].str.lower().str.contains("normal")]) 
        # Retorno com a contagem
        funcoes.cria_log("Contagem fluxo personalizado concluida com sucesso...","autOKRs")
        return [contClientesfluxoNormal]
    except Exception as e:
        print('--> Erro na funcao \'fluxo_personalizado\' <--')
        funcoes.printError(e,"autOKRs")
        return [-1]

def contagem_layouts_documentos(dataFrame:pd.DataFrame,instancesDataFrame:pd.DataFrame) -> list:
    '''
        Funcao
        ------
           Faz a contagem de documentos e layouts a enviar, enviados e com envio atrasado.
        
        Parametros
        ----------
            dataFrame: DataFrame (obrigatorio)
                DataFrame utilizado para contagem.

            instancesDataFrame: DataFrame (obrigatorio)
                DataFrame utilizado para contagem.
        
        Retorno
        -------
            Retorna 2 listas, uma para layouts e uma para documentos, com a quantidade para cada contagem:
            + `[contEnvLayoutPendentes,contEnvLayoutRealizados,contEnvLayoutAtrasadas],[contEnvDocPendentes,contEnvDocRealizados,contEnvDocAtrasados]`
            * Se erro, retorna duas listas contendo o valor `-1`.
    '''
    try:
        funcoes.cria_log("Realizando contagem de Layouts e Documentos...","autOKRs")
        df = dataFrame
        # Envio de Layout Pendentes 
        envLayout = df.loc[(df['requestName'] == 'Projeto  v. 20') & (df['taskName'] == 'Baixar Layout e apresentar ao cliente')]
        contEnvLayoutPendentes = len(envLayout)
        # Envio de Layout Realizados - Contagem por Períodos
        contEnvLayoutRealizados = contagem_Instancias_Orquestra('projeto v.20', 'baixar layout', periodo1, periodo2, instancesDataFrame)
        # Envio de Layout Atrasados
        contEnvLayoutAtrasadas = len(envLayout[(envLayout['taskName'] == 'Baixar Layout e apresentar ao cliente') & (envLayout['taskAtrasada'] == True)])

        # Envio de Documentos Pendentes
        envDoc = df.loc[(df['requestName'] == 'Projeto  v. 20') & (df['taskName'] == 'Entregar Documentação ao Cliente')]
        contEnvDocPendentes = len(envDoc)
        # Envio de Documentos Realizados - Contagem por Períodos
        contEnvDocRealizados = contagem_Instancias_Orquestra('projeto v.20','entregar documentação', periodo1, periodo2, instancesDataFrame)
        # Envio de Documentos Atrasados 
        contEnvDocAtrasados = len(envDoc.loc[envDoc['taskAtrasada'] == True])
        funcoes.cria_log("Contagem de Layouts e Documentos concluida com sucesso...","autOKRs")
        return [contEnvLayoutPendentes,contEnvLayoutRealizados,contEnvLayoutAtrasadas],[contEnvDocPendentes,contEnvDocRealizados,contEnvDocAtrasados]
    except Exception as e:
        print('--> Erro na funcao \'contagem_layouts_documentos\' <--')
        funcoes.printError(e,"autOKRs")
        return [-1,-1,-1],[-1,-1,-1]

def salvar_DataFrame_Excel(df:pd.DataFrame) -> bool:
    try:
        funcoes.cria_log("Salvando dataframe com as contagens...","autOKRs")
        if not(df.empty):
            dt1 = (datetime.today() - timedelta(days=7)).strftime("_%d_%m_%Y")
            dt2 = datetime.today().strftime("_%d_%m_%Y")
            nomeArquivo = "OKRs_CustomerSuccess" + dt1 + dt2 + ".xlsx"

            # Criacao da pasta
            absPathFolder = os.getcwd() + "\\arquivosOkrs\\"

            if not(os.path.exists(absPathFolder)):
                # Pasta nao existe
                print(">> Pasta excel: {} nao existe!".format(absPathFolder))
                print(">> Criando pasta excel...")

                os.mkdir(absPathFolder)
                print(">> Pasta excel criada!")
            else:
                # Pasta existe
                print(">> Pasta excel: {} existe!".format(absPathFolder))

            # Salva arquivo     
            print(">> Salvando arquivo {}...".format(nomeArquivo))
            df.to_excel(absPathFolder + nomeArquivo )

            # Verifica se foi salvo
            if not(os.path.exists(absPathFolder + nomeArquivo)):
                # Arquivo nao foi salvo por algum motivo
                print(">> Nao foi possivel salvar o arquivo!")
                funcoes.cria_log("Nao foi possivel salvar o arquivo...","autOKRs")
                print(">> Fim!")
                return '' , False
            else:
                print(">> Arquivo salvo com sucesso!")
                funcoes.cria_log("Arquivo salvo em: {}...".format(absPathFolder + nomeArquivo),"autOKRs")
                print(">> Fim!")
                return nomeArquivo, True
        else:
            print(">> DataFrame vazio... Nao eh possivel salvar o arquivo!")
            funcoes.cria_log("DataFrame vazio! Nao eh possivel salvar o arquivo...","autOKRs")
            return '', False
    except Exception as e:
        funcoes.printError(e,"autOKRs")
        print(">> Erro ao salvar o arquivo...")
        print(">> Fim!")
        return '', False

def main() -> None:
    funcoes.cria_log("==================================== > NOVA EXECUCAO < ====================================","autOKRs")
    # Para o email
    dt1 = (datetime.today() - timedelta(days=7)).strftime("%d_%m_%Y")
    dt2 = datetime.today().strftime("%d_%m_%Y")
    
    # e-mails
    fileEmails = os.getcwd() + "\\emails.txt"
    if not(fileEmails):
        enviarPara = ["raiulin.borges@elysia.com.br","lukas.machado@elysia.com.br"]
    else:
        with open(os.getcwd() + "\\emails.txt", "r") as f:
            line = str(f.read())
            print(line.rsplit("\n"))
    
    msg = "Período de {0} até {1}.".format(dt1.replace('_','/'), dt2.replace('_','/'))
    assuntoMsg = "Contagem OKRs Customer Success - Periodo: {0} até {1}.".format(dt1.replace('_','/'), dt2.replace('_','/'))

    # Requisicao com dados de atribuicoes aos usuarios
    print(">> Realizando requisicoes...")
    lista = request_Orquestra(method=metodo,urlReq=url,typeReq=tipoUrl,tokens=tks)

    # Confere se a lista esta vazia
    if len(lista) > 0:
        df = formata_DataFrame(lista)

        # Requisicao com dados de instancias
        instancesReport = instances_Report_Orquestra('enb4iHROSDegvkiZv17Fxw%2BkQ7q7Zidu1PKalcpC4o4%3D', True, False, activeInstances=True)
        instancesReportCloseDegs = instances_Report_Orquestra("enb4iHROSDegvkiZv17Fxw%2BkQ7q7Zidu1PKalcpC4o4%3D", True, False, False, False, 255)
        
        # Confere retorno das requisicoes
        if not(instancesReport.empty | instancesReportCloseDegs.empty):
            print(">> Requisicoes realizadas com sucesso!")
            print(">> Realizando contagens...")
            layouts, docs = contagem_layouts_documentos(df, instancesReport)
            contagemCS1 = contagem_CS1(df)
            contagemCS2 = contagem_CS2(df,instancesReport, instancesReportCloseDegs)
            contagemNormal = contagem_fluxo_personalizado(instancesReport)

            listContagens =  contagemCS1 + contagemCS2 + contagemNormal + docs + layouts
            listIndex =['CONTATOS EM ABERTO - CS1', 'CONTATOS EFETIVOS - CS1', 'CONTATOS ATRASADOS - CS1',
                        'CONTATOS EM ABERTO - CS2', 'CONTATOS EFETIVOS - CS2', 'CONTATOS ATRASADOS - CS2',
                        'Nº DE CLIENTES NO ACOMPANHAMENTO PERSONALIZADO',
                        'ENVIOS DE DOCUMENTOS PENDENTES', 'ENVIOS DE DOCUMENTOS REALIZADOS', 'ENVIOS DE DOCUMENTOS ATRASADOS',
                        'ENVIOS DE LAYOUT PENDENTES', 'ENVIOS DE LAYOUT REALIZADOS', 'ENVIOS DE LAYOUT ATRASADOS']
            print(">> Montando dataframe...")
            contagemDF = pd.DataFrame(listContagens, index=listIndex, columns=['Contagem'])

            print(">> Verificando conteudo do dataframe...")
            # DataFrame criado
            if not(contagemDF.empty):
                # Salva arquivo
                print(">> Salvando como Excel o dataframe...")
                # Verifica se arquivo Salvo
                nomeArquivo, salvo = salvar_DataFrame_Excel(contagemDF)
                if not(salvo):
                    # Nao salvo
                    print('>> Nao foi possivel salvar o arquivo excel, verificar log de execucao!')
                    erro = "Nao foi possivel salvar o arquivo excel...\n>> Tempo de Execucao: " + str(time.process_time() - timeStart)
                    localLog, nomeLog, logExiste = funcoes.cria_log(erro,"autOKRs")
                    log = [[localLog, nomeLog, "text/plain"]]

                    # Verifica se log existe
                    if logExiste:
                        log = [[localLog, nomeLog, "text/plain"]]
                        retorno = funcoes.envia_Email(enviarPara, assuntoMsg, erro, "templateOKRsErro.html", log)
                        funcoes.cria_log(retorno,"autOKRs")
                    else:
                        retorno = funcoes.envia_Email(enviarPara, assuntoMsg, erro, "templateOKRsErro.html")
                        funcoes.cria_log(retorno,"autOKRs")
                        print(retorno)
                else:
                    # Envia e Fim
                    print(">> Enviando e-mail...")
                    anexo = [["arquivosOkrs/",nomeArquivo,"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"]]
                    retorno = funcoes.envia_Email(enviarPara, assuntoMsg, msg, "templateOKRs.html", anexo)
                    funcoes.cria_log(retorno,"autOKRs")
                    # Fim
                    print(retorno)
        else:
            print(">> Erro nas requisicoes...")
            erro = "Erro ao realizar requisicao de instancias no orquestra!\n>> Tempo de Execucao:" + str(time.process_time() - timeStart)
            localLog, nomeLog, logExiste = funcoes.cria_log(erro,"autOKRs")

            # Verifica se log existe
            if logExiste:
                log = [[localLog, nomeLog, "text/plain"]]
                print(">> Enviando e-mail...")
                retorno = funcoes.envia_Email(enviarPara, assuntoMsg, erro, "templateOKRsErro.html", log)
            else:
                print(">> Enviando e-mail...")
                retorno = funcoes.envia_Email(enviarPara, assuntoMsg, erro, "templateOKRsErro.html")
        # Fim
        print(retorno)
    else:
        print(">> Erro nas requisicoes...")
        erro = "Erro ao realizar requisicao de solicitacoes no orquestra!\n>> Tempo de Execucao:" + str(time.process_time() - timeStart)
        localLog, nomeLog, logExiste = funcoes.cria_log(erro,"autOKRs")

        # Verifica se log existe
        if logExiste:
            log = [[localLog, nomeLog, "text/plain"]]
            print(">> Enviando e-mail...")
            retorno = funcoes.envia_Email(enviarPara, assuntoMsg, erro, "templateOKRsErro.html", log)
        else:
            print(">> Enviando e-mail...")
            retorno = funcoes.envia_Email(enviarPara, assuntoMsg, erro, "templateOKRsErro.html")

if __name__ == "__main__":
    main()
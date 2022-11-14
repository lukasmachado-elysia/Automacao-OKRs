import requests
import os
from datetime import datetime, timedelta
from dateutil import parser
from flask import Flask, render_template
from flask_mail import Mail, Message


def printError(e, nomeLog:str='erros'):
    print('\n------------------------------------') 
    print('Nao foi possível realizar a operacao!')
    print('------------------------------------\n') 

    templateError = '!!! ---> Um erro do tipo: "{0}" ocorreu <--- !!!\nArgumentos:\n{1}'
    messageError = templateError.format(type(e).__name__,e.args)
    print(messageError)
    cria_log("Erro: ".format(e),"autOKRs")


def requests_API_Orquestra(metodo='GET',urlAcesso="https://elysia.zeev.it",tipoAcesso="/api/2/assignments",head={},payload={}):
    '''
        Funcao
        ------
            Funcao que retorna a requisicao desejada a partir do url de acesso e link de tipo de acesso.
            !Sendo permitido apenas metodos POST e GET!

        Parameters
        ----------

            metodo: str (OPCIONAL)
                Metodo a ser utilizado na requisicao, POST ou GET.
                Se nao for especificado nenhum ele ira utilizar o metodo 'GET'.
            
            urlAcesso: str (OPCIONAL)
                Url usada na requisicao.
                Se nao for especificado nenhum ele ira utilizar o URL que ja esta no funcao.
            
            tipoAcesso: str (OPCIONAL)
                Url de acesso para o tipo de funcao na API, POST ou GET.
                Se nao for especificado nenhum ele ira utilizar o URL que ja esta no funcao.
                Ex.: **/api/2/assignments**
            
            head: str (OBRIGATORIO)
                Autorizacao para acesso da API.
                Ex.: **{'Authorization': 'token_acesso'}**
            
            payload: str (OPCIONAL)
                Parametros para acesso atraves de filtros na requisicao.
        
        Retorno
        -------
            Retorna o objeto response ou resposta de erro caso ocorra.
            Ex.: <Response [200]> 
    '''
    # verifica qual tipo de requisicao foi pedida
    try:
        if metodo == 'GET':
            req = requests.get(url=urlAcesso+tipoAcesso,headers=head,params=payload)
            return req
        elif metodo == 'POST':
            req = requests.post(url=urlAcesso+tipoAcesso,headers=head,params=payload)
            return req
        else: 
            raise NameError('Nenhum metodo valido foi passado. Passe os metodos POST ou GET.')
    except Exception as e:
        print('funcoes')
        printError(e)

def cria_log(msgExecucoes:str,nomePrograma:str):
    """
        Funcao
        ------
            Cria um log de execucao do programa no local: `absolutePathPrograma\\logsPrograma\\log_data_nomePrograma.log`
        
        Parametros
        ----------
            msgExecucoes : str, obrigatorio
                Mensagem de execucao.\n
                * O recomendado eh armazenar em uma string cada mensagem de execucao que voce deseja adicionar no log e no final chamar esta funcao.
            
            nomePrograma : str, obrigatorio
                Nome do programa que sera colocado no log.
   
        Retorno
        -------
            bool : retorna `True` se o log foi criado com sucesso e retorna `False` em caso de excecao ou problema na criacao do arquivo.
    """
    try:
        nomePrograma = nomePrograma
        absPathFolder = os.getcwd() + "\\logsPrograma\\"

        # Criacao da pasta
        if not(os.path.exists(absPathFolder)):
            # Pasta nao existe
            print(">> Pasta: {} nao existe!".format(absPathFolder))
            print(">> Criando pasta...")

            os.mkdir(absPathFolder)
            print(">> Pasta criada!")
        else:
            # Pasta existe
            print(">> Pasta: {} existe!".format(absPathFolder))

        # Criacao do arquivo
        nomeArquivo =  "log_{}_{}.txt".format(datetime.today().strftime("%d_%m_%Y"), nomePrograma)
        print(">> Verificando se {} existe".format(nomeArquivo))

        if not(os.path.exists(absPathFolder + nomeArquivo)):
            # Arquivo nao existe, cria ele e alimenta
            print(">> Nao existe!")
            print(">> Criando arquivo...")
            logMsg = '''-------------------------------------------\n------- LOG DE EXECUCAO DO PROGRAMA -------\n-------------------------------------------\nData e Hora: {0}\nLog:\n>>({0}): {1}\n-------------------------------------------\n\n'''.format(datetime.today().strftime("%d/%m/%Y %Hh:%Mm:%Ss"), msgExecucoes)
            with open(absPathFolder + nomeArquivo, 'w', encoding="utf-8") as file:
                print(">> Escrevendo no arquivo...")
                writeData = file.write(logMsg)
                print(">> writeData: {}".format(str(writeData)))

            # Fecha arquivo
            print(">> Fechando arquivo...")
            file.close()
            if file.closed:
                print(">> Arquivo fechado!")
                return absPathFolder, nomeArquivo, True
            else: 
                print(">> Erro ao fechar o arquivo!\n<!!!> Possivel problema na criacao do log <!!!>")
                return '', '', False
        else:
            # Arquivo ja existe, possivelmente uma nova execucao
            print(">> Arquivo existe!")
            logMsg = ">>({0}): {1}\n".format(datetime.today().strftime("%d/%m/%Y %Hh:%Mm:%Ss"), msgExecucoes)
            with open(absPathFolder + nomeArquivo, 'a', encoding="utf-8") as file:
                print(">> Escrevendo no arquivo...")
                appendData = file.write(logMsg)
                print(">> appendData: {}".format(str(appendData)))

            # Fecha arquivo
            print(">> Fechando arquivo...")
            file.close()
            if file.closed:
                print(">> Arquivo fechado!")
                return absPathFolder, nomeArquivo, True
            else: 
                print(">> Erro ao fechar o arquivo!\n<!!!> Possivel problema na criacao do log <!!!>")
                return '', '', False
    except Exception as e:
        printError(e)
        return '', '', False

def envia_Email(enderecosEnvio:list, assunto:str, mensagem:str, template:str,listAttach:list=[]) -> str:
    '''
        Funcao
        ------

            Envia e-mail para os enderecos de envio especificados na lista.
            * O e-mail `bot.elysia@gmail.com` eh o remetente.
    
        Parametros
        ----------
            enderecosEnvio : list, obrigatorio
                Uma lista dos enderecos de e-mail que receberao o e-mail.
            
            assunto : str, obrigatorio
                O assunto que ira no e-mail.
            
            mensagem : str, obrigatorio
                A mensagem que sera colocada no corpo do e-mail.
            
            template : str, obrigatorio
                Nome do `template.html` que sera utilizado como base para a mensagem
                
            listAttach : list, opcional
                Uma lista composta por sublistas com os anexos: `[ ["caminhoAnexo", "nomeAnexo", "tipoAnexo"], ..., n-sublistAttach ]`.\n\n 
                Para o `tipoAnexo`, verificar documentacao do MDN:\n
                *`https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/MIME_types/Common_types` 
                
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
            msg.html = render_template(template,data=mensagem)
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
        printError(e)
        return ">> Nao foi possivel enviar o email!"
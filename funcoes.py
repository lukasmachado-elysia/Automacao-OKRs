import requests

def printError(e):
    print('\n------------------------------------') 
    print('Nao foi possível realizar a operacao!')
    print('------------------------------------\n') 

    templateError = '!!! ---> Um erro do tipo: "{0}" ocorreu <--- !!!\nArgumentos:\n{1}'
    messageError = templateError.format(type(e).__name__,e.args)
    print(messageError)

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
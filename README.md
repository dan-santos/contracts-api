# Como rodar
1. Dar git pull na sua máquina
2. Ativar um ambiente virtual do python (>= 3.12)
3. Se você tiver make no seu terminal, rode o 3.1, senão, rode o 3.2
    1. make up
    2. docker compose up -d --wait --remove-orphans --build && docker compose logs -f app
(Lembre-se que se você usa linux/MAC, a dependender da sua distro, o comando correto é "docker-compose")


# Decisões técnicas
1. Criação de uma camada de infra adicional além das estabelecidas no enunciado do exercício.
    Tive a necessidade de criar a camada "infra", que é a responsável por:
    1. Implementar os contratos definidos em /repositories
    2. Criar as entidades de dados
    3. Versionar as migrations

    Isso foi feito pois, como estamos usando o SQLModel juntamente com o postgres, queremos isolar ao máximo possível o acoplamento que essas ferramentas externas tem com o nosso domínio de negócio. Aqui, se faz extremamente necessário o uso de Injeções de Dependência no código (similar ao que fiz para fazer a camada de service utilizar os gateways através apenas das interfaces (repositories)).
2. Criação de uma pasta adicional para adicionar configurações de middleware
    Senti a necessidade de criação dessa pasta para conseguir centralizar configurações de logging (como definição dos logs estruturados e do correlation id antes de chegar de fato nas views da aplicação).
2. Uso do SQLModel
    Normalmente, eu utilizo o SQLAlchemy nas aplicações comerciais que já tive contato, mas aqui, preferi usar o SQLModel por uma questão de compatibilidade natural com o FastAPI, o que me ajudou a produzir mais coisas em menos tempo e sem eu ter que ficar me apegando a problemas menos importantes que poderiam ocorrer entre SQLAlchemy e FastAPI.
3. Centralização de tratamento de Exceptions na camada protocolar (nas views).
    Hoje, há N formas em como você pode levantar e tratar exceções dentro do seu projeto. É mais um tema onde não há certo ou errado, mas por uma questão de costume, eu tendo a deixar a aplicação propagar a exception até a camada mais externa, para ai sim, eu tomar uma decisão do que fazer com ela (a única exceção é o explicado no ponto 3.2).
    
    Isso me ajuda a não misturar conceitos que só uma camada deveria conhecer. A título expositivo, cito dois exemplos:
    1. Exceptions de cancelamento/reprocessamento só são tratadas nas views pois não faz sentido eu propagá-las desde a sua origem como uma HTTPException de código 422. O protocolo HTTP é algo específico da camada protocolar. Nem os services, nem a camada infra deveriam saber o que significa um "erro 422".
    2. Na camada de infra, onde há a implementação concreta dos repositories, pode ser que ao buscar um registro que não exista, seja levantada uma Exception de NoResultFound (ou outra correlata advinda do ORM). Aqui, novamente, a Exception precisa ser capturada antes de ser repassada para service e precisamos transformá-la numa Exception de domínio. Não faz sentido a camada de domínio saber/tratar/propagar uma Exception de uma dependência externa (como uma Exception do SQLModel/Postgres).

# Pontos de melhoria
1. Criação de mais testes
    Em virturde do tempo que me foi dado e do tempo livre que dispus para realizá-lo, não conseguir fazer testes unitários em todas as camadas, e testes de todas as complexidades (unitários, intergração, e2e, carga, estresse, etc.). Os únicos que decidi adicionar nesse desafio são os testes da camada de service, pois tratam e focam especificamente nas regras que a API deve seguir. Os demais testes são também importantes, mas os da service layer eu encarei como prioritários.
2. Inclusão do redis como cache
    Eu tendo a utilizar o redis como cache quando a aplicação já está no ar e otimizações de consulta já não são mais suficientes para suportar o volume de requests feitas à aplicação. Somente nesse momento em que penso em adicionar redis.
    Em virtude desse motivo, adicionado ao tempo que tinha disponível para realizar o desafio, optei por não adicionar mais uma dependência externa ao projeto, mas certamente ela seria necessária para deixarmos de fazer tantas operações de leitura nas bases relacionais.
3. Uso de uma biblioteca de pacotes mais robusta.
    Para esse exercício, utilizei o próprio pip do python para focar no que realmente importa, no entanto, em ambiente mais complexos em que a aplicação precisará ser mantida por diversas pessoas, o pip "puro" acaba por ser simples demais e pode gerar diversas confusões, como, por exemplo, não separar de forma apropriada e clara o suficiente o que é dependência de desenvolvimento e o que é dependência de produção. Em ambiente reais, eu tendo a preferir aderir ao poetry como minha escolha padrão.
4. Uso de uma biblioteca/framework mais apropriado para fazermos injeção de dependência.
    Você irá perceber que no arquivo `app/v1/contract/view.py`, ao utilizarmos os services, estamos criando instâncias das classes concretas tanto do service, quanto do gateways que são injetados. Num ambiente produtivo, o ideal é que isso não ocorra, pois faz com que a camada protocolar da aplicação (rest) conheça uma implementação específica das interfaces de service/gateway. Idealmente, o que deveria ser feito é fazer a `view.py` (camada protocolar) utilizar apenas a interface do service, e delegar para uma biblioteca (interna do python ou terceira) em se encarregar de descobrir qual "implementer" ela deve usar em tempo de execução.
    Mesmo com esse ponto de atenção, a definição/implementação dos services e a definição das interfaces dos gateways (repositories) já foram implementadas de maneira agnóstica, de forma que uma troca de framework ou dependências externas não mude em nada dos contratos pré-estabelecidos entre as classes.
5. Uso de uma biblioteca específica para migrations
    Novamente, por conta da simplicidade, aqui, preferi utilizar somente os recursos que o próprio ORM do SQLModel me dá para versionar todas as versões de banco de dados que a minha aplicação usa. No entanto, num ambiente produtivo, eu utilizaria uma biblioteca mais robusta que me permitisse ter mais controle de upgrades, rollbacks e syncs, como, por exemplo, o alembic.
6. Pensar numa lógica otimista para evitar race-conditions.
    Em momentos da implementação dos `repositories`, eu utilizei `selects` que fazem locks pessimistas na base de dados. Isto é, uma vez adquirido o registro, todas as outras requests vão esperar a transação ser completada/dropada até que o registro fique livre do lock. Isso garante que não haverá condições de corrida de N requisições manipulando o mesmo registro ao mesmo tempo. No entanto, isso funciona apenas quando a aplicação é pequena e/ou quando se quer realmente ter uma consistência completa na aplicação em qualquer momento. Em ambientes da aplicações data-intensive, talvez seja melhor partir para uma estratégia de consistência eventual usando, por exemplo, versions/versões da última atualização do registro para decidirmos que irá ter prioridade de acesso/escrita/leitura.
# catholic-bible

[English](README.md)

Uma API somente leitura e um dataset publicado da Bíblia católica. 73 livros,
português, inglês e latim, domínio público do começo ao fim.

Esta é a porta de entrada. O documento em inglês é o completo, com as treze
rotas, o quickstart, o container e a regra de versionamento.

## Os deuterocanônicos são o ponto

O maior conjunto livre de remissões que existe é o OpenBible, 204601 entradas, e
nenhuma delas encosta em Tobias, Judite, Sabedoria, Eclesiástico, Baruc ou os
Macabeus. Em nenhuma das duas direções. Não é descuido de ninguém. O conjunto foi
feito por e para leitores cujo cânon tem 66 livros.

Sobra que as passagens que um leitor católico mais precisa ver ligadas são
justamente as que todo conjunto disponível deixa soltas. Mateus 4,4 cita
Sabedoria 16,26 e nenhuma votação por consenso vai te contar isso.

O que fecha a lacuna aqui são 292 pares de endereços escritos à mão, expandidos
nas duas direções, sem carregar texto de fonte nenhuma. Dão 665 dos 920 elos
deuterocanônicos que sobreviveram.

## O jeito mais barato de entrar

Sem instalar nada, sem chave, sem conta, sem servidor. Cola num arquivo HTML
vazio e abre no navegador.

```js
const book = await (await fetch('https://cdn.jsdelivr.net/gh/ronaldoscotti/catholic-bible@v1.0.1/data/versions/matos-soares/books/SIR.json')).json()
console.log(book.verses['SIR.24.1'].text)
```

Isso é Eclesiástico 24,1 em português, de um livro do cânon que a maior parte
dos dados bíblicos livres não carrega. São 371 arquivos publicados assim, 48 MB,
com três traduções, o Haydock nos dois idiomas, as remissões, o cânon e a
espinha.

O `@v1.0.1` da URL não é enfeite. Fixa a versão e os bytes daquele endereço nunca
mudam. Correção sai como tag nova e a antiga continua respondendo.

### Ou instalando

Os mesmos arquivos saem como pacote, sem código e sem dependência nenhuma.

```sh
npm i the-catholic-bible
```

O parser de referência, o cânon, a espinha e a API vêm em Python.

```sh
pip install the-catholic-bible
```

```py
from catholic_bible.canon.reference import parse_reference

print(parse_reference("Jo 3,16"), parse_reference("Jó 3,16"))
```

`Jo` é João e `Jó` é Jó. O acento nunca é dobrado, que é justamente o erro que
manda o leitor brasileiro para o livro errado.

O nome de instalação e o de importação são diferentes. `pip install
the-catholic-bible` te dá `import catholic_bible`, porque `catholic-bible` no
PyPI é um projeto sem relação com este que chegou lá antes.

Os dois pacotes e o `@v1.0.1` do CDN são a mesma versão, e o número mora num
lugar só.

## O comentário em português

O Haydock traduzido, 20705 notas cobrindo os 73 livros. É a parte deste projeto
que não existe em nenhum outro lugar, e **foi traduzida por um modelo de
linguagem**. O inglês ao lado é a transcrição de 1859 e não foi tocado.

Nenhuma pessoa leu a tradução ainda, e essa é a lacuna mais séria do repositório.
A revisão humana está pendente e é bem-vinda. Uma amostra sorteada de 200
entradas, com o inglês ao lado, espera em
`docs/qa/haydock-translation-sample.csv`. Se você lê português e latim, é a coisa
mais útil que alguém pode contribuir aqui.

## O que este repositório não consegue provar

`LIMITS.md` responde essa pergunta com número medido em vez de promessa. A taxa
de endereços que não caem na espinha, por livro e por esquema. Os doze versículos
que faltam na Douay-Rheims. O que a auditoria de direitos concluiu sobre cada
ativo e o que ficou de fora por causa dela.

`DECISIONS.md` guarda cada escolha difícil com a alternativa que perdeu e o que a
escolha custou. `ROADMAP.md` diz o que vem, `CONTRIBUTING.md` diz como entrar, e
`docs/method/` registra o processo que produziu tudo isso.

Remissões do OpenBible são usadas sob CC BY 4.0.
**Cross-references courtesy of OpenBible.info.** O mesmo aviso viaja dentro de
toda resposta da API que usa esses dados e dentro do dataset publicado, porque
atribuição que só existe no README é atribuição que o consumidor nunca vê.

# Takum_RiskV

Projeto da disciplina deArquitetura e Organização de Computadores desenvolvido por Gabriel Lopes, Lucas Petronilho e Kauan Valente.

A ideia principal é usar o formato de número Takum no lugar do formato padrão (IEEE 754) nas instruções vetoriais do RISC-V. As novas instruções formam a extensão Zvtakum.

Esta é a primeira entrega (até a semana 4). O código é um simulador em Python: ele mostra o resultado de cada instrução, sem simular o hardware

## ARQUIVOS

```
takum.py       # converte entre número comum e Takum
alu.py         # soma, subtração, multiplicação, produto escalar e conversão
vm.py          # instruções vetoriais e contador de instruções
test_takum.py  # testes do takum.py
test_alu.py    # testes do alu.py
test_vm.py     # testes do vm.py
```

## TAKUM

O Takum existe em 3 tamanhos: T8, T16 e T32, os bits são divididos assim:

```
| S | D |  R  |   C   |      F      |
```

- `S`: sinal (positivo ou negativo)
- `D`: indica se o valor é maior ou menor que 1
- `R`: diz quantos bits tem o `C`
- `C`: parte do expoente
- `F`: parte decimal do número

Casos especiais:
- Tudo zero = o número 0
- Só o primeiro bit igual a 1 = NaR 

## CÓDIGO

**takum.py**
- `split_fields`: separa os campos do número
- `decode`: transforma Takum em número comum
- `encode`: transforma número comum em Takum. Arredonda para o valor mais próximo. Se o número for grande ou pequeno demais, usa o maior ou o menor valor possível.

**alu.py**
- `t_add`, `t_sub`, `t_mul`: somar, subtrair e multiplicar
- `t_dot`: produto escalar de duas listas
- `t_cvt`: troca o tamanho do número

Se um dos números for NaR, o resultado também é NaR.

**vm.py**: as instruções vetoriais do enunciado, que fazem a operação em todos os elementos da lista de uma vez. Também conta quantas instruções foram usadas.

`vtadd.vv` = soma
`vtsub.vv` = subtração
`vtmul.vv` = multiplicação
`vtdot.vv` = produto escalar 
`vncvt.t.t` = reduz o tamanho 

## TESTES

- `test_takum.py`: testa a conversão de e para Takum
- `test_alu.py`: testa as operações em T8, T16 e T32
- `test_vm.py`: testa as instruções vetoriais e o contador

Para rodar todos os testes:

```
python -m unittest -v
```

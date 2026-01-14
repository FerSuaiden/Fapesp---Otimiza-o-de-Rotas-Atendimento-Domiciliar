# 📋 RESUMO PARA APRESENTAÇÃO - PARTE 3

## O que foi feito?

**Geração de instâncias sintéticas para testar o modelo de otimização de rotas de Atenção Domiciliar.**

## Por que sintéticas?

Os dados públicos do DATASUS **não têm** o que precisamos:

- ❌ Endereço dos pacientes (protegido pela LGPD)
- ❌ Janela de horário preferida
- ❌ Frequência de visitas individual

Isso é **normal** - toda a literatura científica usa instâncias sintéticas.

## O que TEMOS de dados reais?

| Fonte | Dado | Uso |
|-------|------|-----|
| CNES/DATASUS | Localização das 3.152 equipes EMAD de SP | Posição das equipes |
| IBGE Censo 2022 | População idosa por setor censitário | Distribuir pacientes |
| Portaria 3.005/2024 | Perfil de demanda (70% AD2, 30% AD3) | Proporções realistas |

## Instâncias geradas

| Nome | Pacientes | Equipes | Para quê? |
|------|-----------|---------|-----------|
| pequena_10 | 10 | 1 | Testar se o código funciona |
| pequena_20 | 20 | 2 | Debug rápido |
| media_50 | 50 | 3 | Benchmark |
| media_100 | 100 | 5 | Tamanho típico |
| grande_200 | 200 | 8 | Escalabilidade |
| grande_500 | 500 | 15 | Limite do modelo |

## Fluxo simplificado

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   CNES/DATASUS  │     │   IBGE Censo    │     │  Portaria AD    │
│   (equipes)     │     │   (população)   │     │   (perfil)      │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 ▼
                    ┌────────────────────────┐
                    │  15-gerador_instancias │
                    │       .py              │
                    └────────────┬───────────┘
                                 ▼
                    ┌────────────────────────┐
                    │  instancias/*.json     │
                    │  (6 instâncias)        │
                    └────────────────────────┘
```

## Próximo passo

Usar essas instâncias para rodar o modelo BRKGA (Kummer et al., 2024) e comparar resultados.

---

*Script: `15-gerador_instancias.py` (682 linhas, bem documentado)*

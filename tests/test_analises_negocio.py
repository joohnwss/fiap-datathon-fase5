import copy
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import analises_negocio as a
from test_coortes_regressao import prepared_fixture

ROOT = Path(__file__).resolve().parents[1]


class AnalisesNegocioTests(unittest.TestCase):
    def test_missing_is_not_zero(self):
        s = a.summary([None]*10 + [0]*10 + [8]*10)
        self.assertEqual((s['n'], s['ausentes'], s['media']), (20, 10, 4))
        self.assertIsNone(a.summary([None]*10)['media'])

    def test_small_profiles_and_complementary_suppression(self):
        self.assertNotIn('media', a.summary(range(9)))
        self.assertNotIn('contagens', a.distribution(['a']*99+['b'], ['a','b']))
        self.assertNotIn('rho', a.association(range(9), range(9)))
        groups = a.grouped_summaries({'a': range(9), 'b': range(20), 'c': range(30)})
        self.assertNotIn('total', groups['a'])
        self.assertNotIn('total', groups['b'])
        self.assertEqual(groups['c']['n'], 30)

    def test_partition_rejects_unaccounted_observations(self):
        with self.assertRaises(ValueError):
            a.distribution(['a']*10 + ['outside'], ['a'])

    def test_denominators_and_direction(self):
        d = a.distribution(['a']*10+['b']*30, ['a','b'])
        self.assertEqual(d['denominador'],40)
        self.assertEqual(d['proporcoes']['a'],.25)
        c = a.association([None]+list(range(10)), [0]+list(range(10)))
        self.assertEqual((c['n'],c['total'],c['ausentes_par']),(10,11,1))
        self.assertAlmostEqual(c['rho'],1)
        self.assertIsNone(a.association([1]*10,range(10))['rho'])

    def test_year_adjustment_removes_between_year_signal(self):
        x=list(range(10))+list(range(100,110))
        y=list(range(9,-1,-1))+list(range(109,99,-1))
        self.assertGreater(a.association(x,y)['rho'],0)
        self.assertAlmostEqual(a.association(x,y,[2022]*10+[2023]*10)['rho'],-1)

    def test_phase_and_stone_separate(self):
        rows=prepared_fixture()
        rows[0]['pedra_padronizado']='agata'
        f=a.analytic_frame(rows)
        self.assertEqual(f.iloc[0]['fase'],0)
        self.assertEqual(f.iloc[0]['pedra'],'Ágata')
        self.assertNotIn('ra', f.columns)
        self.assertNotIn('nome', f.columns)

    def test_validated_join_not_position_and_duplicates_fail(self):
        rows=prepared_fixture()
        left,right=a.paired_frames(rows,2022,2023)
        self.assertEqual(right.iloc[0]['ida'],99)
        duplicate=copy.deepcopy(rows[0]); rows.append(duplicate)
        with self.assertRaises(ValueError): a.paired_frames(rows,2022,2023)

    @classmethod
    def setUpClass(cls):
        cls.records=a.load_prepared(ROOT)
        cls.result=a.analyze(cls.records)

    def test_structural_ipp(self):
        self.assertEqual(self.result['ipp']['2022']['status'],'ausencia_estrutural')
        s=self.result['anuais']['2022']['indicadores']['ipp']
        self.assertEqual(s['n'],0); self.assertIsNone(s['media'])
        changed=copy.deepcopy(self.records); changed[0]['ipp_numerico']=0
        with self.assertRaises(ValueError): a.analyze(changed)

    def test_deterministic_without_model_calls(self):
        with patch('modelagem.fit_checked', side_effect=AssertionError('Treino proibido')), patch('modelagem.evaluate_temporal', side_effect=AssertionError('Avaliação proibida')):
            self.assertEqual(self.result,a.analyze(self.records))
            a.official_model(ROOT)

    def test_official_values_read_from_artifacts(self):
        official=json.loads((ROOT/'reports/metricas_modelagem.json').read_text(encoding='utf-8'))
        m=a.official_model(ROOT)
        self.assertEqual(m['temporal'],official['temporal']['metricas'])
        self.assertEqual(m['oof'],official['oof']['metricas'])
        self.assertEqual(m['limiar'],official['limiar'])

    def test_longitudinal_delta_independently(self):
        left,right=a.paired_frames(self.records,2022,2023)
        expected=(right.ida-left.ida).dropna()
        s=self.result['longitudinal']['2022→2023']['mudancas']['ida']
        self.assertEqual(s['n'],len(expected))
        self.assertAlmostEqual(s['media'],float(expected.mean()))

    def test_artifact_schema_integrity_figures(self):
        path=ROOT/a.METRICS
        if not path.exists(): self.skipTest('Executar geração das análises para validar artefatos')
        checks=a.validate_artifacts(ROOT)
        self.assertTrue(checks['analises_11_perguntas'])
        m=json.loads(path.read_text(encoding='utf-8'))
        self.assertEqual(m['analises'],self.result)
        self.assertEqual(len(m['figuras']),10)
        for p in m['figuras']:
            data=(ROOT/p).read_bytes()
            self.assertTrue(data.startswith(b'\x89PNG\r\n\x1a\n'))
            self.assertGreater(len(data),10000)

    def test_public_report_no_individuals_or_absolute_paths(self):
        from relatorio_analises import render_report
        report=render_report(self.result,a.official_model(ROOT),[f'reports/figures/{i}.png' for i in range(10)])
        self.assertEqual(a.public_text_issues(report),[])
        for r in self.records:
            for field in ('ra','nome_padronizado'):
                value=r[field]
                if value and len(value)>=5: self.assertNotIn(value.casefold(),report.casefold())
        for i in range(1,12): self.assertIn(f'## {i}.',report)


if __name__=='__main__': unittest.main()

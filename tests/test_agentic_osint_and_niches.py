"""
test_agentic_osint_and_niches.py // Unit and Integration Tests for OSINT Recon and Universal Niche Dispatcher
Pure Python 3.12 Standard Library (Zero PIP Dependencies)
"""

import unittest
from pathlib import Path
from tooling.agentic.osint_recon import inspect_identity_osint, format_llm_osint_context, OSINTDossier
from tooling.agentic.niche_dispatcher import NicheDispatcher, NicheDispatchResult, REGISTRY_ROOT


class TestOSINTRecon(unittest.TestCase):

    def test_01_empty_handle_handling(self):
        dossier = inspect_identity_osint("")
        self.assertEqual(dossier.handle, "")
        self.assertEqual(dossier.verified_count, 0)
        self.assertEqual(dossier.footprint_score, 0.0)
        self.assertIn("Nenhum identificador", dossier.summary_markdown)

    def test_02_dossier_serialization(self):
        dossier = inspect_identity_osint("torvalds")
        d_dict = dossier.to_dict()
        self.assertEqual(d_dict["handle"], "torvalds")
        self.assertIn("footprint_score", d_dict)
        self.assertIn("summary_markdown", d_dict)
        self.assertIn("verified_profiles", d_dict)
        self.assertGreaterEqual(dossier.verified_count, 1)
        self.assertGreater(dossier.footprint_score, 0.0)

    def test_03_format_llm_osint_context(self):
        dossier = inspect_identity_osint("antoniaci")
        ctx = format_llm_osint_context(dossier)
        self.assertIn("[CONTEXTO OSINT DEEP RECON", ctx)
        self.assertIn("@antoniaci", ctx)
        self.assertIn("[FIM DO CONTEXTO OSINT]", ctx)


class TestNicheDispatcher(unittest.TestCase):

    def setUp(self):
        self.dispatcher = NicheDispatcher(REGISTRY_ROOT)

    def test_01_osint_mention_dispatch(self):
        res = self.dispatcher.dispatch("por favor me fale tudo sobre o @torvalds")
        self.assertEqual(res.niche, "OSINT")
        self.assertEqual(res.target, "torvalds")
        self.assertTrue(res.handled)
        self.assertIn("Dossiê de Inteligência OSINT", res.content_markdown)
        self.assertIn("[CONTEXTO OSINT DEEP RECON", res.enrichment_context)

    def test_02_repo_intel_dispatch(self):
        res = self.dispatcher.dispatch("o que voce sabe sobre o repo @antoniaci/blackbird ?")
        self.assertEqual(res.niche, "REPO_INTEL")
        self.assertEqual(res.target, "antoniaci/blackbird")
        self.assertTrue(res.handled)
        self.assertIn("Inteligência de Repositório", res.content_markdown)
        self.assertIn("[CONTEXTO REPO INTEL", res.enrichment_context)

    def test_03_quantum_squad_dispatch(self):
        res = self.dispatcher.dispatch("chamar o agente @sentinel para auditoria")
        self.assertEqual(res.niche, "QUANTUM_SQUAD")
        self.assertEqual(res.target, "sentinel")
        self.assertTrue(res.handled)
        self.assertIn("Esquadrão Quântico", res.content_markdown)
        self.assertIn("[CONTEXTO QUANTUM SQUAD", res.enrichment_context)

    def test_04_skill_arsenal_dispatch(self):
        res = self.dispatcher.dispatch("preciso do blueprint da skill @blackbird-osint-recon")
        self.assertEqual(res.niche, "SKILL_ARSENAL")
        self.assertEqual(res.target, "blackbird-osint-recon")
        self.assertTrue(res.handled)
        self.assertIn("Arsenal de Habilidades", res.content_markdown)
        self.assertIn("[CONTEXTO SKILL ARSENAL", res.enrichment_context)

    def test_05_cybersecurity_trigger(self):
        res = self.dispatcher.dispatch("avaliar mitigação para CVE-2024-3094 e #security")
        self.assertEqual(res.niche, "CYBER_SECURITY")
        self.assertEqual(res.target, "CVE-2024-3094")
        self.assertTrue(res.handled)
        self.assertIn("Defesa Cibernética Soberana", res.content_markdown)

    def test_06_telemetry_trigger(self):
        res = self.dispatcher.dispatch("status do sistema #telemetry e armadura mark-liv")
        self.assertEqual(res.niche, "TELEMETRY")
        self.assertEqual(res.target, "Mark-LIV")
        self.assertTrue(res.handled)
        self.assertIn("Telemetria Tática da Armadura", res.content_markdown)

    def test_07_general_fallback(self):
        res = self.dispatcher.dispatch("qual e a melhor forma de organizar meu dia de trabalho?")
        self.assertEqual(res.niche, "GENERAL")
        self.assertFalse(res.handled)
        self.assertEqual(res.content_markdown, "")


if __name__ == "__main__":
    unittest.main()

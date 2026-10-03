import pathlib,importlib.util,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location("aid",ROOT/"reference/artifact_identity_adapter.py");m=importlib.util.module_from_spec(sp);sys.modules["aid"]=m;sp.loader.exec_module(m)
class ArtifactIdentityTests(unittest.TestCase):
 def evidence(self,data=b'{"result":"fixture"}'):
  return m.identify_bytes(data,artifact_id="artifact:fixture",origin_repository="DonkeyJJLove/sbom",origin_head="a"*40,producer_id="fixture-producer",media_type="application/json",schema_ref="fixture.schema/v1",app_id="sbom",owner_team="K82M",env="test",app_version="1.0.0")
 def test_actual_bytes_and_origin_are_bound(self):
  e=self.evidence();self.assertEqual(e.validate(b'{"result":"fixture"}'),e);self.assertEqual(e.publication_effect,"NONE")
 def test_tamper_denied(self):
  with self.assertRaises(m.ArtifactIdentityError):self.evidence().validate(b"tampered")
 def test_missing_or_inconsistent_provenance_denied(self):
  e=self.evidence();bad=m.ArtifactIdentityEvidence(**{**e.__dict__,"origin_repository":"Other/repo"})
  with self.assertRaises(m.ArtifactIdentityError):bad.validate()
if __name__=="__main__":unittest.main()

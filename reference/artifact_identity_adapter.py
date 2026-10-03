from __future__ import annotations
from dataclasses import asdict,dataclass
from hashlib import sha256
import json,re
SHA=re.compile(r"^[0-9a-f]{64}$");GIT=re.compile(r"^[0-9a-f]{40}$");REPO=re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
class ArtifactIdentityError(ValueError):pass
@dataclass(frozen=True)
class AID:
 app_id:str;owner_team:str;env:str;vcs_ref:str;app_version:str;repo:str
 def validate(self):
  if not all(isinstance(x,str) and x.strip() for x in (self.app_id,self.owner_team,self.env,self.vcs_ref,self.app_version,self.repo)):raise ArtifactIdentityError("aid")
  if REPO.fullmatch(self.repo) is None:raise ArtifactIdentityError("aid repo")
  return self
@dataclass(frozen=True)
class ArtifactIdentityEvidence:
 artifact_id:str;aid:AID;origin_repository:str;origin_head:str;producer_id:str;media_type:str;schema_ref:str;byte_length:int;bytes_sha256:str;authority_effect:str="NONE";publication_effect:str="NONE"
 def validate(self,data:bytes|None=None):
  self.aid.validate()
  if not isinstance(self.artifact_id,str) or not self.artifact_id.strip():raise ArtifactIdentityError("artifact_id")
  if REPO.fullmatch(self.origin_repository) is None or self.aid.repo!=self.origin_repository:raise ArtifactIdentityError("origin")
  if GIT.fullmatch(self.origin_head) is None or self.aid.vcs_ref!=self.origin_head:raise ArtifactIdentityError("origin_head")
  if not all(isinstance(x,str) and x.strip() for x in (self.producer_id,self.media_type,self.schema_ref)):raise ArtifactIdentityError("metadata")
  if isinstance(self.byte_length,bool) or not isinstance(self.byte_length,int) or self.byte_length<0:raise ArtifactIdentityError("byte_length")
  if not isinstance(self.bytes_sha256,str) or SHA.fullmatch(self.bytes_sha256) is None:raise ArtifactIdentityError("digest")
  if self.authority_effect!="NONE" or self.publication_effect!="NONE":raise ArtifactIdentityError("effects")
  if data is not None and (len(data)!=self.byte_length or sha256(data).hexdigest()!=self.bytes_sha256):raise ArtifactIdentityError("byte mismatch")
  return self
 def canonical_bytes(self):
  self.validate();return json.dumps(asdict(self),sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
def identify_bytes(data:bytes,*,artifact_id:str,origin_repository:str,origin_head:str,producer_id:str,media_type:str,schema_ref:str,app_id:str,owner_team:str,env:str,app_version:str)->ArtifactIdentityEvidence:
 if not isinstance(data,bytes):raise ArtifactIdentityError("data")
 aid=AID(app_id,owner_team,env,origin_head,app_version,origin_repository).validate()
 return ArtifactIdentityEvidence(artifact_id,aid,origin_repository,origin_head,producer_id,media_type,schema_ref,len(data),sha256(data).hexdigest()).validate(data)

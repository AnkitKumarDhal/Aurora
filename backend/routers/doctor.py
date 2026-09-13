from fastapi import APIRouter

router = APIRouter()

# TODO: doctor-side routes — queue, patient case view, approve/edit
# All routes here require Depends(require_role("doctor")) from auth.dependencies
# See docs/api-contract.md section 5 for the contract this needs to satisfy

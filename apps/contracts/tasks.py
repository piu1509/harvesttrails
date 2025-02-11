from __future__ import absolute_import, unicode_literals

from celery import shared_task

from apps.contracts.DocusignEmbedded import DocusignEmbeddedSigningController
from apps.contracts.models import GrowerContracts
from apps.grower.models import Grower
from apps.contracts.models import Contracts
from apps.accounts.models import User

from apps.docusign.tokens import get_docusign_token


@shared_task(name='create_envelope_growers')
def create_envelope_and_store(contract_id, username, return_url):
    user = User.objects.get_by_natural_key(username)
    contract = Contracts.objects.get(pk=contract_id)
    growers = Grower.objects.all().order_by('-id')
    for grower in growers[:2]:
        try:
            embedded = DocusignEmbeddedSigningController()
            document_list, tabs = embedded.get_document_list_from_envelope_id_with_tabs(contract.envelope_id)
            envelope_args = {
                "signer_email": grower.email,
                "signer_name": grower.name,
                "signer_client_id": grower.id,
                "ds_return_url": str(grower.id).join(return_url.rsplit(str(contract_id), 1)),
            }
            args = {
                "account_id": DocusignEmbeddedSigningController.account_id,
                "base_path": DocusignEmbeddedSigningController.base_path,
                "access_token": get_docusign_token()['access_token'],
                "envelope_args": envelope_args
            }
            results = DocusignEmbeddedSigningController.worker_envelope_id(document_list, tabs, args)
            grower_contract = GrowerContracts.objects.create(contract=contract,
                                                             contract_url=results['redirect_url'],
                                                             grower=grower,
                                                             created_by=user,
                                                             envelope_id=results['envelope_id'],
                                                             envelope_uri=results['envelope_uri']
                                                             )
            print(grower_contract)
            grower_contract.save()
        except Exception as err:
            return print(err)

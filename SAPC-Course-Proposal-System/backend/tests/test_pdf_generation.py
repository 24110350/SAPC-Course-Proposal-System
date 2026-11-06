import os
from pathlib import Path
from app.services.pdf_service import PDFGenerator

def test_pdf_generation_file_creation(tmp_path, valid_proposal_payload):
    payload = valid_proposal_payload.copy()
    payload['proposal_id'] = 'SAPC-TEST-0099'
    payload['status'] = 'Under Review'

    filepath, filename = PDFGenerator.generate_proposal_pdf(payload, output_dir=tmp_path)
    
    # Assert file exists and has size
    pdf_file = Path(filepath)
    assert pdf_file.exists()
    assert pdf_file.name == 'SAPC-TEST-0099.pdf'
    assert pdf_file.stat().st_size > 1000

    # Assert PDF header magic bytes %PDF
    with open(filepath, 'rb') as f:
        header = f.read(4)
        assert header == b'%PDF'

def test_pdf_download_endpoint(client, valid_proposal_payload):
    payload = valid_proposal_payload.copy()
    payload['course_title'] = "PDF Download Test Course"
    create_res = client.post('/api/proposals', json=payload)
    assert create_res.status_code == 201
    prop_id = create_res.get_json()['proposal']['proposal_id']

    # Download PDF
    pdf_res = client.get(f'/api/proposals/{prop_id}/pdf')
    assert pdf_res.status_code == 200
    assert pdf_res.mimetype == 'application/pdf'
    assert f"{prop_id}.pdf" in pdf_res.headers.get('Content-Disposition', '')
    assert len(pdf_res.data) > 1000
    assert pdf_res.data[:4] == b'%PDF'

def test_pdf_view_inline_endpoint(client, valid_proposal_payload):
    payload = valid_proposal_payload.copy()
    payload['course_title'] = "PDF Inline View Test Course"
    create_res = client.post('/api/proposals', json=payload)
    assert create_res.status_code == 201
    prop_id = create_res.get_json()['proposal']['proposal_id']

    # View PDF inline
    pdf_res = client.get(f'/api/proposals/{prop_id}/pdf/view')
    assert pdf_res.status_code == 200
    assert pdf_res.mimetype == 'application/pdf'
    assert 'attachment' not in pdf_res.headers.get('Content-Disposition', '').lower()
    assert pdf_res.data[:4] == b'%PDF'

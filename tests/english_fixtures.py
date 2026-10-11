"""Explicit English review for unrelated lifecycle fixtures, never production data.

Unknown synthetic Chinese prose receives a visibly synthetic translation; dedicated
bilingual tests use real source/translation pairs and assert their exact semantics.
"""
import re
from backend.knowledge import content_workspace as ws,locale

def fixture_fields(review):
    values={}
    for source,value in review['fields'].items():
        values[source]=value or 'Synthetic fixture text: '+' '.join(re.findall(r'https?://[^\s)\]<>]+|[A-Za-z][A-Za-z0-9._-]*\d[A-Za-z0-9._-]*|(?<![\w])\d+(?:[.,]\d+)*(?:%|[kKmMbB])?',source))
    return values

def approve_fixture(kind,ident):
    current=ws.detail(kind,ident)
    if current['english']['state']=='reviewed':return current
    if not current['english']['source_hash']:return current
    return ws.english_review(kind,ident,{'draft_version':current['draft_version'],'source_hash':current['english']['source_hash'],
        'fields':fixture_fields(current['english']),'confirmed':True,'reason':'Explicit English approval for isolated lifecycle fixture'})

def reviewed_preview(kind,ident):
    try:approve_fixture(kind,ident)
    except (ValueError,KeyError,TypeError):pass # Preserve malformed-draft feedback from the real preview.
    return ws.preview(kind,ident)

def reviewed_merge(data):
    from backend.knowledge import stewardship as st
    first=st.preview(data)
    reviews={ident:{'source_hash':r['source_hash'],'fields':fixture_fields(r),'confirmed':True,'reason':'Isolated bilingual merge review'}
             for ident,r in first['english_reviews'].items() if r['state']!='reviewed'}
    data={**data,**({'english_reviews':reviews} if reviews else {})}
    return data,st.preview(data)

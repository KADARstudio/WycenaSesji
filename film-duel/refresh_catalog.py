"""Poland-only, subscription-only catalogue for a private, non-commercial prototype.
Uses the public website's unofficial interface, not the licensed Partner API.
A failed refresh never changes the timestamp of the last successful catalogue.
"""
import concurrent.futures
import datetime as dt
import json
import pathlib
import time
import urllib.error
import urllib.request
API = 'https://apis.justwatch.com/graphql'
HERE = pathlib.Path(__file__).resolve().parent
WANTED = [('netflix',['Netflix']),('prime',['Amazon Prime Video']),('disney',['Disney Plus','Disney+']),('max',['HBO Max','Max']),('apple',['Apple TV','Apple TV Plus','Apple TV+']),('sky',['SkyShowtime'])]
def graphql(query, variables=None):
    payload = json.dumps({'query':query,'variables':variables or {}}).encode()
    for attempt in range(3):
        try:
            req = urllib.request.Request(API,data=payload,headers={'Content-Type':'application/json','Accept':'application/json','User-Agent':'Seans-PrivatePrototype/0.1 (non-commercial catalogue test)'})
            with urllib.request.urlopen(req,timeout=40) as response: result=json.load(response)
            if result.get('errors'): raise ValueError(json.dumps(result['errors'],ensure_ascii=False))
            return result['data']
        except (urllib.error.URLError,TimeoutError):
            if attempt==2: raise
            time.sleep(2**attempt)
QUERY='''query Movies($packages: [String!]!) {
 popularTitles(country: PL, first: 100, sortBy: POPULAR,
 filter: {objectTypes: [MOVIE], packages: $packages, monetizationTypes: [FLATRATE]}) {
 totalCount
 edges { node { id
 content(country: PL, language: pl) {
 title fullPath originalReleaseYear runtime shortDescription posterUrl
 genres { shortName translation(language: pl) }
 scoring { imdbScore imdbVotes }
 externalIds { imdbId }
 }
 offers(country: PL, platform: WEB, filter: {monetizationTypes: [FLATRATE]}) {
 standardWebURL monetizationType package { shortName clearName }
 }
 } }
 }
}'''
def main():
    packages=graphql('query { packages(country: PL, platform: WEB) { shortName clearName } }')['packages']
    providers=[]
    for key,names in WANTED:
        found=next((p for name in names for p in packages if p['clearName'].casefold()==name.casefold()),None)
        if not found: raise ValueError(f'Cannot resolve Polish provider {key}; candidates: {packages}')
        providers.append({'id':key,'code':found['shortName'],'name':found['clearName']})
    print('Polish services:',json.dumps(providers,ensure_ascii=False))
    mapping={p['code']:p['id'] for p in providers}
    fetched_at=dt.datetime.now(dt.timezone.utc).isoformat()
    def fetch_provider(provider):
        result=graphql(QUERY,{'packages':[provider['code']]})['popularTitles']
        entries=[]
        for edge in result['edges']:
            node=edge['node']; c=node['content']
            if not c.get('fullPath','').startswith('/pl/'): raise ValueError('Non-Polish title path')
            offers=[]; used=set()
            for o in node.get('offers',[]):
                service=mapping.get(o['package']['shortName']); url=o.get('standardWebURL','')
                if service and service not in used and o['monetizationType']=='FLATRATE' and url.startswith('https://'):
                    used.add(service); offers.append({'provider':service,'name':o['package']['clearName'],'url':url})
            if provider['id'] not in used: continue
            score=c.get('scoring') or {}; poster=c.get('posterUrl') or ''
            entries.append({'id':node['id'],'title':c['title'],'year':c.get('originalReleaseYear'),'runtime':c.get('runtime'),'description':c.get('shortDescription') or '', 'poster':('https://images.justwatch.com'+poster.replace('{profile}','s592').replace('{format}','jpg')) if poster else '', 'url':'https://www.justwatch.com'+c['fullPath'],'genres':[{'id':g['shortName'],'name':g['translation']} for g in c.get('genres',[])],'rating':score.get('imdbScore'),'votes':score.get('imdbVotes'),'imdbId':(c.get('externalIds') or {}).get('imdbId'),'offers':offers})
        if not entries: raise ValueError(f'No verified Polish subscription films for {provider["name"]}')
        print(provider['name'],'total:',result['totalCount'],'sample:',len(entries))
        return entries
    movies={}
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        for entries in executor.map(fetch_provider,providers):
            for movie in entries:
                if movie['id'] not in movies: movies[movie['id']]=movie
                else:
                    old=movies[movie['id']]; codes={o['provider'] for o in old['offers']}
                    old['offers'].extend(o for o in movie['offers'] if o['provider'] not in codes)
    if len(movies)<50: raise ValueError('Suspiciously small catalogue; keeping previous file')
    result={'version':1,'country':'PL','monetization':'FLATRATE','fetchedAt':fetched_at,'refreshHours':1,'source':'JustWatch public website data (unofficial, non-commercial prototype)','sampleLimitPerProvider':100,'providers':providers,'movies':list(movies.values())}
    temp=HERE/'catalog.tmp.json'; temp.write_text(json.dumps(result,ensure_ascii=False,separators=(',',':')),encoding='utf-8'); temp.replace(HERE/'catalog.json')
    print(f'Validated {len(movies)} films, fetched {fetched_at}')
if __name__=='__main__': main()

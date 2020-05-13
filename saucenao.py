#!/usr/bin/env python3 -u
import asyncio
import uvloop
import aiohttp
import ujson
#################CONFIG##################
api_key = 'bef587aaba257b80bc5188c618743c03ef62f6d7'
EnableRename = False
##############END CONFIG#################
index_hmags = '0'
index_reserved = '0'
index_hcg = '0'
index_ddbobjects = '0'
index_ddbsamples = '0'
index_pixiv = '1'
index_pixivhistorical = '1'
index_reserved = '0'
index_seigaillust = '0'
index_danbooru = '0'
index_drawr = '0'
index_nijie = '0'
index_yandere = '1'
index_animeop = '0'
index_reserved = '0'
index_shutterstock = '0'
index_fakku = '0'
index_hmisc = '0'
index_2dmarket = '0'
index_medibang = '0'
index_anime = '0'
index_hanime = '0'
index_movies = '0'
index_shows = '0'
index_gelbooru = '0'
index_konachan = '1'
index_sankaku = '0'
index_animepictures = '0'
index_e621 = '0'
index_idolcomplex = '0'
index_bcyillust = '0'
index_bcycosplay = '0'
index_portalgraphics = '0'
index_da = '0'
index_pawoo = '0'
index_madokami = '0'
index_mangadex = '0'


class saucenao():

    # generate appropriate bitmask
    db_bitmask = int(index_mangadex+index_madokami+index_pawoo+index_da+index_portalgraphics+index_bcycosplay+index_bcyillust+index_idolcomplex+index_e621+index_animepictures+index_sankaku+index_konachan+index_gelbooru+index_shows+index_movies+index_hanime+index_anime+index_medibang +
                     index_2dmarket+index_hmisc+index_fakku+index_shutterstock+index_reserved+index_animeop+index_yandere+index_nijie+index_drawr+index_danbooru+index_seigaillust+index_anime+index_pixivhistorical+index_pixiv+index_ddbsamples+index_ddbobjects+index_hcg+index_hanime+index_hmags, 2)
    url = 'http://saucenao.com/search.php?output_type=2&numres=5&dbmask=' + \
        str(db_bitmask)+'&api_key='+api_key+'&url='

    async def search(self, img_url):
        async with aiohttp.ClientSession(trust_env=True) as session:
            async with session.get(self.url+img_url) as resp:
                if resp.status != 200:
                    if resp.status == 403:
                        print(
                            'Incorrect or Invalid API Key! Please Edit Script to Configure...')
                    else:
                        # generally non 200 statuses are due to either overloaded servers or the user is out of searches
                        print("status code: "+str(resp.status_code))
                    return
                else:
                    results = ujson.loads(await resp.text())
                    if int(results['header']['user_id']) > 0:
                        # api responded
                        print('Remaining Searches 30s|24h: '+str(
                            results['header']['short_remaining'])+'|'+str(results['header']['long_remaining']))
                        if int(results['header']['status']) == 0:
                            # search succeeded for all indexes, results usable
                            print('search succeeded for all indexes, results usable')
                        else:
                            if int(results['header']['status']) > 0:
                                # One or more indexes are having an issue.
                                # This search is considered partially successful, even if all indexes failed, so is still counted against your limit.
                                # The error may be transient, but because we don't want to waste searches, allow time for recovery.
                                print('API Error. Retrying in 600 seconds...')
                            else:
                                # Problem with search as submitted, bad image, or impossible request.
                                # Issue is unclear, so don't flood requests.
                                print(
                                    'Bad image or other request error. Skipping in 10 seconds...')
                            return
                    else:
                        # General issue, api did not respond. Normal site took over for this error state.
                        # Issue is unclear, so don't flood requests.
                        print('Bad image, or API failure. Skipping in 10 seconds...')
                        return
                r_list = []
                for i in range(results['header']['results_returned']):
                    r = results['results'][i]
                    # one or more results were returned
                    if float(r['header']['similarity']) > float(results['header']['minimum_similarity']):
                        print(
                            'hit! '+r['header']['similarity'])
                        # get vars to use
                        r_dist = {}
                        r_dist['similarity'] = r['header']['similarity']
                        r_dist['p_img'] =r['header']['thumbnail']
                        r_dist['s_url'] = r['data']['ext_urls']
                        if r['header']['index_id'] == 5 or r['header']['index_id'] == 6:
                            r_dist['s_name'] = 'Pixiv'
                            r_dist['s_id'] = r['data']['pixiv_id']
                            r_dist['s_title'] = r['data']['title']
                        elif r['header']['index_id'] == 26:
                            r_dist['s_name'] = 'Konachan'
                            r_dist['s_id'] = r['data']['konachan_id']
                            r_dist['s_title'] = r['data']['creator']
                        elif r['header']['index_id'] == 12:
                            r_dist['s_name'] = 'Yande'
                            r_dist['s_id'] = r['data']['yandere_id']
                            r_dist['s_title'] = r['data']['creator']
                        r_list.append(r_dist)
                    else:
                        print(
                            'miss... '+str(r['header']['similarity']))
                        return
        return r_list
                # could potentially be negative
                # if int(results['header']['long_remaining']) < 1:
                #     print('Out of searches for today. Sleeping for 6 hours...')
                #     return -1
                # if int(results['header']['short_remaining']) < 1:
                #     print(
                #         'Out of searches for this 30 second period. Sleeping for 25 seconds...')
                #     return -2

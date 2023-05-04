import asyncio
import signal
import functools
import aiohttp
import os
import datetime
import matplotlib
import sys
import json
matplotlib.use('Agg')
import matplotlib.pyplot as plt


WATCH_URLS = os.environ.get('WATCH_URLS')
WATCH_INTERVAL = os.environ.get('INTERVAL') or 1
OUT_DIR = os.environ.get('OUT_DIR')
UPLOAD_URL = 'https://sm.ms/api/upload'

class bcolors:  
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

async def watch_task(loop, url):
    print("{}Init watching {}{}".format(bcolors.OKBLUE, url, bcolors.ENDC))
    times = []
    status = []
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36'}
        async with aiohttp.ClientSession(loop=loop,
                                         conn_timeout=10,
                                         read_timeout=10,
                                         raise_for_status=True,
                                         headers=headers) as session:
            while True:
                
                t = datetime.datetime.now()
                try:
                    async with session.get(url) as resp:
                            if resp.status in range(200,299):
                                times.append(t)
                                status.append(0)
                except (aiohttp.ClientResponseError,
                            aiohttp.ClientConnectionError,
                            asyncio.TimeoutError):
                    times.append(t)
                    status.append(1)
                finally:
                    await asyncio.sleep(WATCH_INTERVAL)

    except asyncio.CancelledError:
        return { 'time' : times , 'status' : status, 'url' : url }
 
 
async def shutdown(sig, loop):
    print("{}\nWatching stopped, calculating data....{}\n".format(bcolors.OKGREEN, bcolors.ENDC))
    tasks = [task for task in asyncio.all_tasks() if task is not
             asyncio.current_task()]
    list(map(lambda task: task.cancel(), tasks))
    results = await asyncio.gather(*tasks, return_exceptions=True)
    #print('finished awaiting cancelled tasks, results: {0}'.format(results))
    file_path = await plot_result(results)
    await upload_img(loop, file_path)
    
    loop.stop()
    

async def plot_result(data):
    file_path = "{}/stats-man_{}.png".format(OUT_DIR,
                                            datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
    labels = []
    fig, ax = plt.subplots()
    for r in data:
        labels.append(r['url'])
        ax.plot(r['time'], r['status'])

    plt.xlabel('Time', labelpad=20)
    plt.ylabel('Responds')
    plt.yticks([0,1], ('success','fail'))
    ax.set_ylim([0,1])
    ax.xaxis_date()
    ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter('%H:%M:%S'))
    ax.xaxis.set_major_locator(matplotlib.dates.SecondLocator(interval=10 * WATCH_INTERVAL))
    ax.xaxis.set_minor_locator(matplotlib.dates.SecondLocator(interval=WATCH_INTERVAL))
    fig.autofmt_xdate()
    plt.legend(labels, loc='upper right')
    plt.savefig(file_path, dpi=300)
    plt.close()
    print("{}Report save to {}{}".format(bcolors.OKGREEN, file_path, bcolors.ENDC))
    return file_path


async def upload_img(loop, file_path):
    async with aiohttp.ClientSession(loop=loop,
                                    raise_for_status=True) as session:
        try:
            fd = aiohttp.FormData()
            fd.add_field('smfile',
                        open(file_path, 'rb'),
                        content_type='image/png')
            async with session.post(UPLOAD_URL, data=fd) as resp:
                data = await resp.json()
                if data['code'] == 'success':
                    print("{}Report URL: {}{}\n".format(bcolors.OKGREEN,
                                                        data['data']['url'],
                                                        bcolors.ENDC))
                else:
                    print("{}Upload report failed.{}\n".format(bcolors.FAIL, bcolors.ENDC))
                    print("{}{}{}\n".format(bcolors.FAIL,
                                                        data,
                                                        bcolors.ENDC))

        except (aiohttp.ClientResponseError,
                    aiohttp.ClientConnectionError,
                    asyncio.TimeoutError):
            print("{}Upload report failed.{}\n".format(bcolors.FAIL, bcolors.ENDC))



def main():
    # init
    if not WATCH_URLS:
        print("{}Missing WATCH_URLS environment variables.{}\n".format(bcolors.FAIL, bcolors.ENDC))
        sys.exit(1)
    global WATCH_INTERVAL
    WATCH_INTERVAL = int(WATCH_INTERVAL)

    loop = asyncio.get_event_loop()
    for url in WATCH_URLS.split(','):
        asyncio.ensure_future(watch_task(loop, url), loop=loop)

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig,
                            functools.partial(asyncio.ensure_future,
                                            shutdown(sig, loop)))

    # start watch
    print("{}Started watching, press Ctrl+C to stop.{}\n".format(bcolors.OKGREEN, bcolors.ENDC))
    loop.run_forever()
    
    loop.close()
    sys.exit(0)

if __name__ == "__main__":
    main()
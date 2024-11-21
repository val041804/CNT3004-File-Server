# python module that collects statistics from our server module
import psutil
import time
# creating a timer for collecting statistics
# and then printing results after timer is over
def collect_transfer_rates(duration=30):
  start = psutil.net_io_counters()
  time.sleep(duration)
  end = psutil.net_io_counters()
  sent_data = end.bytes_sent - start.bytes_sent
  received_data = end.bytes_recv - start.bytes_recv
  # metrics are in bytes per second
  upload_rate = sent_data / duration
  download_rate = received_data / duration

  return upload_rate, download_rate

print(collect_transfer_rates())

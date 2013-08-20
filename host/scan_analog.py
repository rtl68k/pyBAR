from analysis.plotting.plotting import plot_occupancy
import pprint
import time
import struct
import itertools
import logging

import tables as tb
import BitVector

from analysis.data_struct import MetaTable
from utils.utils import get_all_from_queue, split_seq

from scan.scan import ScanBase

class AnalogScan(ScanBase):
    def __init__(self, config_file, definition_file = None, bit_file = None, device = None, scan_identifier = "scan_analog", outdir = None):
        super(AnalogScan, self).__init__(config_file, definition_file, bit_file, device, scan_identifier, outdir)
        
    def start(self, configure = True):
        super(AnalogScan, self).start(configure)
        
        print 'Start readout thread...'
        #self.readout.set_filter(self.readout.data_record_filter)
        self.readout.start()
        print 'Done!'
        
        
        commands = []
        self.register.set_global_register_value("PlsrDAC", 40)
        commands.extend(self.register.get_commands("wrregister", name = ["PlsrDAC"]))
        self.register_utils.send_commands(commands)
        
        #import cProfile
        #pr = cProfile.Profile()
        mask = 6
        repeat = 100
        wait_cycles = 336*2/mask*24/4*3
        cal_lvl1_command = self.register.get_commands("cal")[0]+BitVector.BitVector(size = 40)+self.register.get_commands("lv1")[0]+BitVector.BitVector(size = wait_cycles)
        #pr.enable()
        self.scan_utils.base_scan(cal_lvl1_command, repeat = repeat, mask = mask, dcs = [], same_mask_for_all_dc = True, hardware_repeat = True, digital_injection = False, read_function = None)#self.readout.read_once)
        #pr.disable()
        #pr.print_stats('cumulative')
        
        q_size = -1
        while self.readout.data_queue.qsize() != q_size:
            time.sleep(0.5)
            q_size = self.readout.data_queue.qsize()
        print 'Items in queue:', q_size
              
        def get_cols_rows(data_words):
            for item in self.readout.data_record_filter(data_words):
                yield ((item & 0xFE0000)>>17), ((item & 0x1FF00)>>8)
                
        def get_rows_cols(data_words):
            for item in self.readout.data_record_filter(data_words):
                yield ((item & 0x1FF00)>>8), ((item & 0xFE0000)>>17)
        
        #data_q = get_all_from_queue(self.readout.data_queue)
        data_q = list(get_all_from_queue(self.readout.data_queue)) # make list, otherwise itertools will use data
        data_words = itertools.chain(*(data_dict['raw_data'] for data_dict in data_q))
        print 'got all from queue'
        
    #    with open('raw_data_digital_self.raw', 'w') as f:
    #        f.writelines([str(word)+'\n' for word in data_words])
    
        total_words = 0
        
        filter_raw_data = tb.Filters(complib='blosc', complevel=5, fletcher32=False)
        filter_tables = tb.Filters(complib='zlib', complevel=5, fletcher32=False)
        with tb.openFile(self.scan_data_path+".h5", mode = "w", title = "test file") as file_h5:
            raw_data_earray_h5 = file_h5.createEArray(file_h5.root, name = 'raw_data', atom = tb.UIntAtom(), shape = (0,), title = 'raw_data', filters = filter_raw_data)
            meta_data_table_h5 = file_h5.createTable(file_h5.root, name = 'meta_data', description = MetaTable, title = 'meta_data', filters = filter_tables)
            
            row_meta = meta_data_table_h5.row
                        
            #data_q = list(get_all_from_queue(scan.readout.data_queue))
            for item in data_q:
                raw_data = item['raw_data']
#                for word in raw_data:
#                    print FEI4Record(word, 'fei4a')
                len_raw_data = len(raw_data)
                for data in split_seq(raw_data, 50000):
                    #print len(data)
                    raw_data_earray_h5.append(data)
                    raw_data_earray_h5.flush()
#                     raw_data_earray_h5.append(raw_data)
#                     raw_data_earray_h5.flush()
                row_meta['timestamp'] = item['timestamp']
                row_meta['error'] = item['error']
                row_meta['length'] = len_raw_data
                row_meta['start_index'] = total_words
                total_words += len_raw_data
                row_meta['stop_index'] = total_words
                row_meta.append()
                meta_data_table_h5.flush()
        
        print 'Stopping readout thread...'
        self.readout.stop()
        print 'Done!'
         
        print 'Data remaining in memory:', self.readout.get_fifo_size()
        print 'Lost data count:', self.readout.get_lost_data_count()
        
        #cols, rows = zip(*get_cols_rows(data_words))
        #plot_occupancy(cols, rows, max_occ = repeat*2)
        
        plot_occupancy(*zip(*get_cols_rows(data_words)), max_occ = repeat*2, filename = None)
        
    
    #    set nan to special value
    #    masked_array = np.ma.array (a, mask=np.isnan(a))
    #    cmap = matplotlib.cm.jet
    #    cmap.set_bad('w',1.)
    #    ax.imshow(masked_array, interpolation='nearest', cmap=cmap)
        
        
if __name__ == "__main__":
    import scan_configuration
    scan = AnalogScan(config_file = scan_configuration.config_file, bit_file = scan_configuration.bit_file, outdir = scan_configuration.outdir)
    scan.start()

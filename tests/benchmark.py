import math
from skrecovery import helpers

def main():
    expected_duration_in_ms = 3001
    benchmark: helpers.Benchmark = helpers.Benchmark('benchmark', 'tests.csv')
    
    # start the benchmark and wait for 1 second
    benchmark.start() 
    helpers.wait(1)
    print('included')
    
    # pause the benchmark and wait for 1 second
    benchmark.pause()
    helpers.wait(1) # this should not be included in the benchmark
    print('excluded')
    
    # resume the benchmark and wait for 1 second
    benchmark.resume()
    helpers.wait(1)
    print('included')
    
    # pause the benchmark and wait for 1 second
    benchmark.pause()
    helpers.wait(1) # this should not be included in the benchmark
    print('excluded')
    
    # resume the benchmark and wait for 1 second
    benchmark.resume()
    helpers.wait(1)
    print('included')
    
    # end the benchmark and print the results
    benchmark.end()
    
    print('total duration:', benchmark.total(), 'ms')
    print(benchmark.entries)
    assert math.ceil(benchmark.total()) == expected_duration_in_ms
    benchmark.save()
    
    
if __name__ == '__main__':
    main()
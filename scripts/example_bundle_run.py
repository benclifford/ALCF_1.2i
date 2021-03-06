import json
import sys
import os

sys.path.append('/mnt/scripts')
import instcat_trimmer as ict
import job_bundling_utils as jbu

# this Python script is functionally a walkthrough for how one would go about trimming
# a group of instance catalogs, output a file that contains all necessary work to be done,
# and then apply it through the FFD job bundling algorithm. It further demonstrates how you might
# check job success and reincorporate unrun jobs.

# To test this in small scale on a Singularity shell, utilize the following command:
# "singularity shell -B /path/to/ALCF_1.2i/inputs:/mnt/cwd,/path/to/ALCF_1.2i/scripts:/mnt/scripts,
#     /path/to/ALCF_1.2i/outputs:/mnt/outputs,/path/to/restarts:/mnt/restarts
#     /path/to/ALCF_1.2i/imsim.simg"
#

# first, we set a group of instcat files to be ingested. Let's choose two for speed.
# Note that the paths here are important; these need to match your later ingest into imSim for
# singularity input binds.
instcat_list_a = ['/mnt/cwd/DC2-R1-2p-WFD-g/000000/instCat/phosim_cat_159479.txt', 
                 '/mnt/cwd/DC2-R1-2p-WFD-g/000001/instCat/phosim_cat_159480.txt']

# We then want to find out what work needs to be done on this sensor. To do that,
# we use the instcat_trimmer module. This requires the imsim python package,
# which is why this is divided into a separate module from the remaining workflow. It
# can be expensive to run on many groups, but is trivially parallelized (split up the instcat inputs)
ict.determine_instcat_work(instcat_list_a, '/mnt/scripts/instcat_worklist_a.json')

# With all the work to be done found, we then want to determine some initial bundling scheme.
# To do this, we call on the job_bundling_utils module. Let's read in that json file.
with open('/mnt/scripts/instcat_worklist_a.json') as fp:
    worklist_a = json.load(fp)

# We need to define the max number of threads and max number of instances per node for this. We choose
# the fiducial values from Theta. Note that the max_instances_node is a non-trivial calculation.
# We assume 10 GB memory per imSim call + 1 GB per thread + 5 GB floating for sharp increases.
# This may vary depending on your version of imSim and architecture.

max_threads_node = 64
max_instances_node = 10
bundle_list_a = jbu.determine_bundles(worklist_a, max_threads_node, max_instances_node)

# This bundle list can be saved and used for your workflow of choice!
with open('/mnt/scripts/bundle_worklist_a.json', 'w') as fp:
    json.dump(bundle_list_a, fp)

# We want to be able to check if a job has outputs. Since we haven't started the job,
# this should fail all those tests. But we can test this with our utilities!

infile = '/mnt/scripts/bundle_worklist_a.json' # the path to our file to check
outpath = '/mnt/outputs/'                       # the path to out imSim outputs
restartpath = '/mnt/restarts/'                  # where we are putting all our restarts

# This checks for the existence of a gzipped file WHILE not having a checkpoint to measure
# success, for each sensor that has work to do. Otherwise, it returns that information into
# a new json file for restarting off of, in the requested restart path.
jbu.check_job_success(infile, outpath, restartpath)

# Let's make a new set of work to also do real quick.
instcat_list_b = ['/mnt/cwd/DC2-R1-2p-WFD-g/000003/instCat/phosim_cat_159492.txt',
                 '/mnt/cwd/DC2-R1-2p-WFD-g/000004/instCat/phosim_cat_159493.txt']
ict.determine_instcat_work(instcat_list_b, '/mnt/scripts/instcat_worklist_b.json')
with open('/mnt/scripts/instcat_worklist_b.json') as fp:
    worklist_b = json.load(fp)
bundle_list_b = jbu.determine_bundles(worklist_b, max_threads_node, max_instances_node)
with open('/mnt/scripts/bundle_worklist_b.json', 'w') as fp:
    json.dump(bundle_list_b, fp)

# And now let's combine THIS with our restart data to generate a new master bundling.
worklist_new = jbu.determine_remaining_jobs('/mnt/scripts/bundle_worklist_b.json', restartpath)
bundle_list_new = jbu.determine_bundles(worklist_new, max_threads_node, max_instances_node)

# And we can just save this new work list!
with open('/mnt/scripts/bundle_worklist_new.json', 'w') as fp:
    json.dump(bundle_list_new, fp)

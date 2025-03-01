#!/bin/bash
#SBATCH --ntasks=3                    # How many jobs
#SBATCH --job-name=sandbox    # Job name
#SBATCH --time=08:00:00               # Time limit hrs:min:sec
#SBATCH --cpus-per-task=2                    # How many jobs
#SBATCH --mem-per-cpu=5G                    # How many jobs
#SBATCH --output=/mnt/nfs/home/aiilyas/slurm/logs/master_log.log
#SBATCH --nodelist=deep-gpu-10

set -e
# . /mnt/nfs/modules/Modules/init/bash
# source ~/.bashrc

# module load conda
# module load mslurm
# module load blender
# conda init bash
# conda activate /mnt/nfs/home/aiilyas/conda_envs/sandbox-release

# FOLDER="$HOME/synthetic-sandbox"

# cd $FOLDER
# file where we will put the hostname and port of master
RANDOM_FILE="$HOME/slurm/interproc/$(openssl rand -base64 12 | sed  's/[^a-z0-9A-Z]//g')"
echo $RANDOM_FILE
export PYTHONPATH=$(pwd)/synthetic-sandbox:$PYTHONPATH
export CIFAR_CLASS=cat
srun --nodes=1 --cpus-per-task=1 --mem-per-cpu=5G --exclusive --ntasks=1 --resv-ports=1 bash -c "
    echo \$(hostname):\$SLURM_STEP_RESV_PORTS > $RANDOM_FILE;
    ulimit -n 50000;
    export PYTHONPATH=$FOLDER:\$PYTHONPATH;
    echo $BLENDER_DATA $YAML_CONFIG $OUTPUT_FOLDER \$SLURM_STEP_RESV_PORTS;
    python threedb/main.py $BLENDER_DATA $YAML_CONFIG $OUTPUT_FOLDER \$SLURM_STEP_RESV_PORTS --single-model;
" &

# Works up until here
master_pid=$!
# Unload conda and load blender for workers
echo 'Now I am here'
for i in $(seq 3 $SLURM_NTASKS); do
    echo $i
    srun --nodes=1 --mem-per-cpu=1G --exclusive --ntasks=1 --cpus-per-task=1 bash -c "
        while [ ! -f $RANDOM_FILE ]; do sleep 1; echo 'waiting for $RANDOM_FILE'; done
        echo 'done waiting';
        sleep 20; # Gives a bit of time to the master to start
        MASTER_URL=\$(cat $RANDOM_FILE);
        echo 'masterurl' \$MASTER_URL;
        export PYTHONPATH=$FOLDER:\$PYTHONPATH;
        blender --python-use-system-env -b -P threedb/client.py -- $BLENDER_DATA --master-address \$MASTER_URL 
    " &
done
echo "SPAWNED"
# Wait for the master to be done
wait $master_pid

rm $RANDOM_FILE
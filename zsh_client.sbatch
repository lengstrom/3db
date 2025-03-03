#!/usr/bin/zsh
#SBATCH --ntasks=3                    # How many jobs
#SBATCH --job-name=sandbox    # Job name
#SBATCH --time=08:00:00               # Time limit hrs:min:sec
#SBATCH --cpus-per-task=2                    # How many jobs
#SBATCH --mem-per-cpu=5G                    # How many jobs
#SBATCH --output=/mnt/nfs/home/engstrom/slurm_logs/log.log

#. /mnt/nfs/modules/Modules/init/zsh
#module load conda
#module load mslurm

#conda init zsh
# source ~/.zshrc
#conda activate /mnt/nfs/home/aiilyas/conda_envs/sandbox-release

echo chungus $CONDA_DEFAULT_ENV
echo $PYTHONPATH

FOLDER=~/src/synthetic-sandbox # /mnt/nfs/home/leclerc/threedbrelease"

cd $FOLDER
# file where we will put the hostname and port of master
RANDOM_FILE="~/slurm/interproc/$(openssl rand -base64 12 | sed  's/[^a-z0-9A-Z]//g')"
echo $RANDOM_FILE
export PYTHONPATH=$(pwd)/synthetic-sandbox:$PYTHONPATH
export CIFAR_CLASS=cat
export BLENDER_DATA=/mnt/nfs/home/datasets/3DB_models
echo $SLURM_STEP_RESV_PORTS

cd ~/src/synthetic-sandbox;

srun --nodes=1 --cpus-per-task=1 --mem-per-cpu=5G --exclusive --ntasks=1 --resv-ports=1 zsh -c "
    echo \$(hostname):\$SLURM_STEP_RESV_PORTS > $RANDOM_FILE;
    ulimit -n 50000;
    cd $FOLDER;
    echo \$SLURM_STEP_RESV_PORTS;
    echo $CIFAR_CLASS;
    echo $BLENDER_DATA;
    export PYTHONPATH=$FOLDER:\$PYTHONPATH;
    python threedb/main.py $BLENDER_DATA $YAML_CONFIG $OUTPUT_FOLDER\
        \$SLURM_STEP_RESV_PORTS --single-model;
" &

# Works up until here
master_pid=$!
# Unload conda and load blender for workers
echo 'Now I am here'
for i in $(seq 3 $SLURM_NTASKS); do
    echo $i
    srun --nodes=1 --mem-per-cpu=1G --exclusive --ntasks=1 --cpus-per-task=1 zsh -c "
        cd $FOLDER;
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

echo "HIHIHIHIHI"
rm $RANDOM_FILE

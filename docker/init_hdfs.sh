#!/bin/sh
# Initialize only a brand-new empty NameNode volume; never reset existing HDFS data.
set -eu
name_dir=/tmp/hadoop-hadoop/dfs/name
data_dir=/tmp/hadoop-hadoop/dfs/data
mkdir -p "$name_dir" "$data_dir"
chown -R 1000:100 "$name_dir" "$data_dir"
chmod 700 "$name_dir" "$data_dir"
if [ -f "$name_dir/current/VERSION" ]; then
    echo 'Existing formatted NameNode volume preserved.'
elif [ -n "$(find "$name_dir" -mindepth 1 -maxdepth 1 -print -quit)" ]; then
    echo 'NameNode volume is nonempty but unformatted; refusing to reset it.' >&2
    exit 2
else
    echo 'Formatting confirmed-empty NameNode volume.'
    sudo -E -u hadoop /opt/hadoop/bin/hdfs namenode -format -nonInteractive
fi

#!/bin/bash
set -x

function main {

  init_params "$@"
  run_tuning

}

# init params
function init_params {

  for var in "$@"
  do
    case $var in
      --topology=*)
          topology=$(echo $var |cut -f2 -d=)
      ;;
      --dataset_location=*)
          dataset_location=$(echo $var |cut -f2 -d=)
      ;;
      --input_model=*)
          input_model=$(echo $var |cut -f2 -d=)
      ;;
      --output_model=*)
          output_model=$(echo $var |cut -f2 -d=)
      ;;
      *)
          echo "Error: No such parameter: ${var}"
          exit 1
      ;;
    esac
  done

}

# run_tuning
function run_tuning {
    # sed -i "/root:/s|root:.*|root: $dataset_location/val|g" conf.yaml
    sed -i "/valid=/s|valid=.*|valid=$dataset_location/coco/5k.txt|g" config/coco.data
    sed -i "/train=/s|train=.*|train=$dataset_location/coco/trainvalno5k.txt|g" config/coco.data
    sed -i "/names=/s|names=.*|names=$dataset_location/coco.names|g" config/coco.data
    current_dir="$PWD"
    cd $dataset_location/coco
    paste <(awk "{print \"$PWD\"}" <5k.part) 5k.part | tr -d '\t' > 5k.txt
    cd $current_dir
    extra_cmd=""

    python test.py \
            --weights_path $input_model \
            --batch_size 128 \
            -t \
            ${extra_cmd}

}

main "$@"

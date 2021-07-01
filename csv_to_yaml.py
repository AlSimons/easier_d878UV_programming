import argparse
import csv
import yaml


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--csv-file', default='channels.csv',
                        help="The CSV file to convert to YAML")
    parser.add_argument('-y', '--yaml-file', default='generated_channels.yaml',
                        help="The YAML file to write")
    args = parser.parse_args()
    return args


def csv_to_dict_list(csv_file):
    dict_list = []
    with open(csv_file) as f:
        reader = csv.DictReader(f)
        for row in reader:
            d = {}
            for k in row.keys():
                d[k] = row[k]
            dict_list.append(d)

    return dict_list



def dict_list_to_yaml(dict_list, yaml_file):
    with open(yaml_file, 'w') as f:
        print(yaml.dump(dict_list), file=f)


def main():
    args = parse_args()
    d = csv_to_dict_list(args.csv_file)
    dict_list_to_yaml(d, args.yaml_file)


if __name__ == '__main__':
    main()

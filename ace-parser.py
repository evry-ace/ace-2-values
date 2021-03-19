#!/usr/bin/env python3

import argparse
import base64
import copy
import json
import os
import sys

from deepmerge import always_merger
from docker_image import reference
import yaml


def _dbg(s: str):
    print("[ace] %s" % s)


def _as_yml(d: dict):
    print(yaml.dump(d))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--ace')
    parser.add_argument('--img-url')
    parser.add_argument("--output", default="/src/out")

    args = parser.parse_args()

    if args.ace is not None and args.ace.endswith(".yaml"):
        _dbg("Read from file")
        with open(args.ace) as fh:
            cfg_contents = fh.read()
    else:
        cfg_contents = base64.urlsafe_b64decode(args.ace)

    cfg = yaml.safe_load(cfg_contents)

    helm = cfg["helm"]
    helm["name"] = cfg["name"]
    helm.setdefault("repo", "https://evry-ace.github.io/helm-charts")
    helm.setdefault("repoName", "ace")

    helm.setdefault("values", {})
    helm["values"].setdefault("name", cfg["name"])

    _dbg("Helm settings")
    _as_yml(helm)

    for name, values in cfg["environments"].items():
        root_values = copy.deepcopy(helm["values"])

        env_settings = copy.deepcopy(cfg["environments"][name])

        _dbg("Env settings")
        _as_yml(env_settings)

        merged = always_merger.merge(root_values, env_settings.get("values", {}))

        img = reference.Reference.parse(args.img_url)
        image = {
            # "repository": image(image_info),
            "repository": img["name"],
            "tag": img["tag"]
        }

        merged.setdefault("image", {})
        merged["image"].update(**image)

        _dbg("Env values")
        _as_yml(merged)

        ns = helm.get("namespace", env_settings.get("namespace", "default"))
        cluster = helm.get("cluster", env_settings.get("cluster", "kubernetes"))

        env_target_values = {
            "namespace": ns,
            "cluster": cluster,
        }
        _as_yml(env_target_values)

        with open("%s/target.%s.yaml" % (args.output, name), 'w') as fh:
            fh.write(yaml.dump(env_target_values))
            fh.close()

        deployment_values = yaml.dump(merged, indent=2)
        with open("%s/values.%s.yaml" % (args.output, name), 'w') as fh:
            fh.write(deployment_values)
            fh.close()

    target_values = {
        "name": helm["name"],
        "chart": helm["chart"],
        "version": helm["version"],
        "repo": helm["repo"],
        "repoName": helm["repoName"]
    }

    with open("%s/target.yaml" % args.output, "w") as fh:
        fh.write(yaml.dump(target_values))
        fh.close()

if __name__ == '__main__':
    main()

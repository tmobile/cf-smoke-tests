# cf-smoke-tests: A Custom Smoke-Tests suite for multi-foundation Cloud-Foundry setup
This smoke-tests suite is a "template", containing pipelines, configurations, sample-apps, and scripts, 
that can be used to monitor the health of various critical Cloud-Foundry components, workflows and marketplace services. 


This repo has the following Components -

## 1. Pipelines -
1. `bootstrap-smoke-test-pipeline` - This deploys `smoke-test-pipeline` on the specific concourse/team paths that are dedicated for each CF foundation.
2. `smoke-test-pipeline` - Runs on each of the foundation specific concourse/team paths, contains jobs corresponding to every service specific smoke-test.

## 2. Environments -
The environments directory contains foundations-specific param files and a common-params file. These files need to be customized based on the overall PCF deployment.

## 3. Smoke-Tests scripts -
The scripts that test the end-to-end workflows involving various types of service-instances and sample apps that interact with those service instances.

## 4. Sample Apps - 
These apps are simple light weight apps that are used by the smoke-tests scripts to test the app-workflows with service-instances.


# How to use this in your own CF setup
This suite can be deployed on a multi-foundation CF setup by following the steps below -
1. Clone this repo and upload it on your organization's internal github.
2. Rename the directories inside `environments/`  with the names of CF foundations in your environment.
3. Update foundation specific parameters in `environments/*/pipeline-vars.yml` files.
4. Replace placeholders such as `FOUNDATION1`, with the CF foundation names in `bootstrap-smoke-test-pipeline` under `params` section.
5. Update the github-url in the `bootstrap-smoke-test-pipeline` and `smoke-test-pipeline.yml` files.
6. Save, commit and push the above changes in your internal repo.
7. Create or ensure the presence of the following keys in Vault or other secret-management tool (These keys should be accessible by the `bootstrap-smoke-test-pipeline`) -
```
CONCOURSE_PASSWORD_FOR_{YOUR-FOUNDATION1}
CONCOURSE_PASSWORD_FOR_{YOUR-FOUNDATION2}
```
8. Create or ensure the presence of the following keys in Vault or other secret-management tool for each foundation (These keys should be accessible by the `smoke-test-pipeline`) -
```
- PIVNET_API_TOKEN - API_TOKEN to download products from Pivnet.
- GIT_PRIVATE_KEY - Private Key to your own internal github where you will host this repo.
- SMOKE_USER - CF user that should have `OrgManager` role on `smoke-org` and `system` orgs.
- SMOKE_PASSWORD - Password for SMOKE_USER.
```
9. Deploy bootstrap pipeline- `fly -t {concourse-target-for-bootstrap-pipeline} sp -p bootstrap-smoke-test-pipeline -c ci/pipelines/bootstrap-smoke-test-pipeline.yml -l environments/global-pipeline-vars.yml`. Unpause and let the deploy job run. It will deploy `smoke-test-pipeline` on all the foundations added under `environments/`.
10. Create `smoke-org` in every foundation added in step 2-3. Create all the `*_SMOKE_SPACE` mentioned in `global-pipeline-vars.yml`.
11. If you don't intend to run specific smoke-test jobs in the smoke-test-pipeline, you can remove those jobs from `smoke-test-pipeline.yml` before deploying the bootstrap pipeline.
12. Let `smoke-test-pipeline` run and check for params related errors. Once those are fixed, the pipeline jobs should run fine, unless there is a valid problem with the foundation.
13. In every smoke-test script, you might want to replace `send_metric_to_influxdb` at the end, with other result-reporter methods or comment it if you don't intend to export results. In `report_results.py` you would need to update the urls for metrics platform that you want to use.

## To start running the smoke-test-pipeline on a new foundation -
1. Simply create `environments/{new-foundation-name}/pipeline-vars.yml` file, copy the params from any other foundation's param file and make the necessary changes.
2. Create or ensure the presence of the params menetioned above in vault.
5. Set the fly target to `{concourse-url}`, `{team-name}` team.
6. Run - `fly -t {concourse-target-for-bootstrap-pipeline} sp -p bootstrap-smoke-test-pipeline -c ci/pipelines/bootstrap-smoke-test-pipeline.yml -l environments/global-pipeline-vars.yml`.

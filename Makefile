DOCKER = docker
ROCM_TORCH_BASE_IMAGE="rocm-torch"
ROCM_TORCH_ADDON_BASE_IMAGE="rocm-torch-addon"

DOCKER_USER=${USER}
DOCKER_GID=$(shell id -g)
DOCKER_UID=$(shell id -u)
DOCKER_TIMEZONE="Asia/Seoul"

OK_COLOR=\033[32;01m
NO_COLOR=\033[0m
# Include volumes configuration
include volumes.conf
# Construct the volume arguments dynamically from the configuration
VOLUME_ARGS=$(foreach volume,$(VOLUMES),--volume=$(volume))

.PHONY: buildtorch-rocm-addon runtorch-rocm-addon help clean

help:
	@echo $(VOLUME_ARGS)
	@echo "Usage: make help | buildtorch-rocm | buildtorch-rocm-addon | runtorch-rocm | runtorch-rocm-addon"
	@echo ""
	@echo "Targets:"
	@echo "  help: Show this help message"
	@echo "  BUILD: make buildtorch-rocm-addon will build the ${ROCM_TORCH_ADDON_BASE_IMAGE}:latest image"
	@echo "  RUN: make runtorch-rocm-addon will run the ${ROCM_TORCH_ADDON_BASE_IMAGE}:latest image"
	@echo "  CLEAN: make clean this wiill trigger a complete build, including the base container"

update_sudoers:
	@echo "Backing up the sudoers file..."
	@cp ./sudoers.orig ./sudoers
	@echo "Updating the sudoers file to replace 'REPLACEUSER' with '${USER}'..."
	@sed -i 's/^REPLACEUSER /${USER} /g' ./sudoers

buildtorch-rocm: update_sudoers
	@echo "$(OK_COLOR)==>$(NO_COLOR) Building ${ROCM_TORCH_BASE_IMAGE}:latest"
	@docker build --no-cache --network=host \
		--build-arg USER=${DOCKER_USER} \
		--build-arg GID=${DOCKER_GID} \
		--build-arg UID=${DOCKER_UID} \
		--build-arg TIMEZONE=${DOCKER_TIMEZONE} \
		--rm -f torch_rocm.df -t ${ROCM_TORCH_BASE_IMAGE}:latest .  2>&1 | tee ./build_torch.log
	@touch .buildtorch-rocm.done

buildtorch-rocm-addon: .buildtorch-rocm.done
	@echo "$(OK_COLOR)==>$(NO_COLOR) Building ${ROCM_TORCH_ADDON_BASE_IMAGE}:latest"
	@docker --debug build --no-cache --network=host \
		--build-arg USER=${DOCKER_USER} \
		--build-arg GID=${DOCKER_GID} \
		--build-arg UID=${DOCKER_UID} \
		--build-arg BASE_IMAGE=${ROCM_TORCH_BASE_IMAGE} \
		--rm -f torch_rocm_addon.df -t ${ROCM_TORCH_ADDON_BASE_IMAGE}:latest .  2>&1 | tee ./build_torch_addon.log

.buildtorch-rocm.done: .pipinstall.done
	$(MAKE) buildtorch-rocm


.pipinstall.done:
	@echo "$(OK_COLOR)==>$(NO_COLOR) Installing pip packages"
	@pip install -r ./requirements.txt"  2>&1 | tee ./pip_install.log
	@touch .pipinstall.done

runtorch-rocm-addon:
	@docker run --shm-size=1g --network host -it --device /dev/kfd --device /dev/dri --group-add video --security-opt seccomp=unconfined --rm \
		--env="DISPLAY" --env="QT_X11_NO_MITSHM=1" --env="USER=${USER}" -env="UID=${UID}" \
		--volume="/tmp/.X11-unix:/tmp/.X11-unix:rw" \
		--volume /sys/fs/cgroup:/sys/fs/cgroup:ro  \
		$(VOLUME_ARGS) \
		--name ${ROCM_TORCH_ADDON_BASE_IMAGE} ${ROCM_TORCH_ADDON_BASE_IMAGE}:latest bash

clean:
	@rm -f ./sudoers
	@rm -f .pipinstall.done
	@rm -f .buildtorch-rocm.done

clean-log:
	@rm -f ./build_torch.log
	@rm -f ./build_torch_addon.log
	


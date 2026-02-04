Summary:	Zigbee to MQTT bridge
Name:		zigbee2mqtt
Version:	2.8.0
Release:	1
License:	GPL v3+
Group:		Applications
Source0:	https://github.com/Koenkk/zigbee2mqtt/archive/%{version}/%{name}-%{version}.tar.gz
# Source0-md5:	61fc19fb92cd78f70f2ca3d6374f4806
# tar -xf zigbee2mqtt-%{version}.tar.gz
# npm -C zigbee2mqtt-%{version} install --ignore-scripts --cpu noarch --no-audit --no-fund --no-update-check
# find zigbee2mqtt-%{version}/node_modules -type d -name prebuilds -prune -exec rm -r {} +
# tar -C zigbee2mqtt-%{version} -acf zigbee2mqtt-node_modules-%{version}.tar.xz node_modules
Source1:	%{name}-node_modules-%{version}.tar.xz
# Source1-md5:	7b7407802e0a172215e8d63f0b8a8616
Source2:	%{name}.service
URL:		https://www.zigbee2mqtt.io
BuildRequires:	libstdc++-devel
BuildRequires:	nodejs-gyp
BuildRequires:	nodejs-typescript
BuildRequires:	npm
BuildRequires:	tar >= 1:1.22
BuildRequires:	xz
Requires(postun):	/usr/sbin/groupdel
Requires(postun):	/usr/sbin/userdel
Requires(pre):	/bin/id
Requires(pre):	/usr/bin/getgid
Requires(pre):	/usr/sbin/groupadd
Requires(pre):	/usr/sbin/useradd
Requires:	nodejs
Suggests:	mosquitto
Provides:	group(zigbee2mqtt)
Provides:	user(zigbee2mqtt)
ExclusiveArch:	%{ix86} %{x8664} %{arm} aarch64
BuildRoot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)

%description
zigbee2mqtt allows you to use your Zigbee devices without the vendor's
bridge or gateway. It bridges events and allows you to control your
Zigbee devices via MQTT. In this way you can integrate your Zigbee
devices with whatever smart home infrastructure you are using.

%prep
%setup -q -a1

grep -r '#!.*env node' -l . | xargs %{__sed} -i -e '1 s,#!.*env node,#!/usr/bin/node,'

%build
export CC="%{__cc}"
export CXX="%{__cxx}"
export CPPFLAGS="%{rpmcppflags}"
export CFLAGS="%{rpmcflags}"
export CXXFLAGS="%{rpmcxxflags}"
export LDFLAGS="%{rpmldflags}"
IFS="
"
for mod_dir in `find node_modules -name binding.gyp -printf '%h\n'`; do
	node-gyp -C "$mod_dir" --nodedir=/usr configure
	node-gyp -C "$mod_dir" --release --verbose -j %{__jobs} build
done
npm run build

%install
rm -rf $RPM_BUILD_ROOT

install -d $RPM_BUILD_ROOT{%{_libdir}/%{name},%{systemdunitdir},%{_sharedstatedir}/%{name}}

cp -pr dist index.js lib node_modules package.json $RPM_BUILD_ROOT%{_libdir}/%{name}
IFS="
"
for mod_dir in `find $RPM_BUILD_ROOT%{_libdir}/%{name}/node_modules -name binding.gyp -printf '%h\n'`; do
	%{__mv} "$mod_dir"/build{,.old}
	install -d "$mod_dir"/build/Release
	%{__mv} "$mod_dir"/build{.old/Release/*.node,/Release}
	%{__rm} -r "$mod_dir"/build.old
done

%{__sed} -e 's;@@DATADIR@@;%{_libdir}/%{name};g' \
	-e 's;@@STATEDIR@@;%{_sharedstatedir}/%{name};g' \
	%{SOURCE2} > $RPM_BUILD_ROOT%{systemdunitdir}/%{name}.service

npm -C $RPM_BUILD_ROOT%{_libdir}/%{name} prune --omit=dev --no-audit --no-fund

cp -p data/configuration.example.yaml $RPM_BUILD_ROOT%{_sharedstatedir}/%{name}/configuration.yaml

%clean
rm -rf $RPM_BUILD_ROOT

%pre
%groupadd -g 355 zigbee2mqtt
%useradd -d /usr/share/empty -u 355 -g zigbee2mqtt -c "zigbee2mqtt bridge" -s /bin/false zigbee2mqtt

%postun
if [ "$1" = "0" ]; then
	%userremove zigbee2mqtt
	%groupremove zigbee2mqtt
fi

%files
%defattr(644,root,root,755)
%doc CHANGELOG.md README.md
%{_libdir}/%{name}
%{systemdunitdir}/%{name}.service
%dir %attr(750,zigbee2mqtt,zigbee2mqtt) %{_sharedstatedir}/%{name}
%attr(640,zigbee2mqtt,zigbee2mqtt) %config(noreplace) %verify(not md5 mtime size) %{_sharedstatedir}/%{name}/configuration.yaml

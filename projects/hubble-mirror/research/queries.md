# 検索と訂正の記録

取得日: 2026-11-03。公式（NASA / ESA / STScI）を先に当たり、論文と参照資料で裏を取った。

## 検索語

- Hubble Space Telescope launch date orbit altitude period NASA
- Hubble mirror 2.4 m 828 kg ULE glass specifications
- Hubble first light May 20 1990 blurry star
- Hubble mirror flaw 2.2 micrometers spherical aberration announcement June 27 1990
- Hubble null corrector field lens 1.3 mm metering rod cap
- Hubble servicing mission 1 STS-61 five spacewalks total EVA hours
- COSTAR WFPC2 first corrected image M100 1994
- Hubble Deep Field 1995 342 exposures 150 orbits 4 filters
- Hubble Deep Field galaxies 1500 3000 full moon 1/30 coin 75 feet
- Roger Angel Hubble 1.3 mm ruler

## 当たった資料

公式: `nasa-optics` / `nasa-observatory` / `nasa-first-light` / `nasa-mirror-flaw` /
`nasa-sm1-timeline` / `nasa-hdf` / `nasa-10-years` / `esa-sm1` / `esa-hdf` /
`stsci-1994-01` / `stsci-1996-01`。

論文・参照: `ntrs-allen`（NASA-TM-103443）/ `nature-346-599` / `physics-today-blurry`。

作品内: `hubble-script`（v12 台本）/ `hubble-review-facts`（v12 の門の記録）。

## 訂正

前の案の値を、次のように直した。

| 前の値 | 直した値 | 出典 |
|---|---|---|
| STS-61 の総船外活動 28.5 時間 | **35 時間 28 分** | `esa-sm1` / `nasa-sm1-timeline` |
| 高度 559km | **約 483km、周期 約95分** | `nasa-observatory` |
| 表面の凹凸 10nm | **1µm 未満**（10nm は使わない） | `nasa-optics` |
| 天域の比較を「10円玉」 | **硬貨**（75 フィート先） | `nasa-hdf` / `esa-hdf` |
| ファーストライトの日付が曖昧 | **1990年5月20日** | `nasa-first-light` |
| 不具合の公表日が無い | **1990年6月27日** | `nasa-mirror-flaw` |

HDF の値も取り直した: **1995年12月18–28日、342 露出、150 周の軌道を予定、
4 フィルター、100 時間超、1,500 → 約3,000 銀河、1996年1月15日公開**。

## 分からなかったこと

- 99.8% と 97% は**作品内の値**で、外部資料の数字ではない。分母は台本の記録に置く。
- 「紙のラベル」と「折れた端」は台本の場面装置で、外部資料の事実ではない。
  `facts.yaml` でも `in-work` として分ける。

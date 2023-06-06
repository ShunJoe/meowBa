import matplotlib.pyplot as plt
from sklearn import mixture
import numpy as np
from skimage.morphology import convex_hull_image

def saveplot(figpath_and_name, dataset):

    fig, ax=plt.subplots(1, 3, figsize=(10, 4))
    ax[0].imshow(dataset[dataset.shape[0]//2,:,:])
    ax[1].imshow(dataset[:,dataset.shape[1]//2, :])
    ax[2].imshow(dataset[:,:,dataset.shape[2]//2])
    plt.savefig(figpath_and_name)


def slice_by_slice_mask_calc(data):
    '''calculate mask from convex hull of data, slice by slice in x-direction'''

    mask=np.zeros(data.shape)
    no_slices=data.shape[0]
    for i in range(no_slices):
        xslice=data[i,:,:]
        mask[i,:,:]=convex_hull_image(xslice)
    return mask


def plot_center_slices(volume, title='', fig_external=[],figsize=(15,5), cmap='viridis', colorbar=False, vmin=None, vmax=None):
        shape=np.shape(volume)

        if len(fig_external)==0:
            fig,ax = plt.subplots(1,3, figsize=figsize)
        else:
            fig = fig_external[0]
            ax = fig_external[1]

        fig.suptitle(title)
        im=ax[0].imshow(volume[:,:, int(shape[2]/2)], cmap=cmap, vmin=vmin, vmax=vmax)
        ax[0].set_title('Center z slice')
        ax[1].imshow(volume[:,int(shape[1]/2),:], cmap=cmap, vmin=vmin, vmax=vmax)
        ax[1].set_title('Center y slice')
        ax[2].imshow(volume[int(shape[0]/2),:,:], cmap=cmap, vmin=vmin, vmax=vmax)
        ax[2].set_title('Center x slice')

        if colorbar:
            fig.subplots_adjust(right=0.8)
            cbar_ax = fig.add_axes([0.85, 0.15, 0.05, 0.7])
            fig.colorbar(im, cax=cbar_ax)


def perform_GMM_np(data_np, n_components, plot=False, n_init=1, nbins=500, title='', fig_external=[], return_labels=False):

    #reshape data
    n_samples=len(data_np)
    X_train = np.concatenate([data_np.reshape((n_samples, 1)), np.zeros((n_samples, 1))], axis=1)

    # fit a Gaussian Mixture Model
    clf = mixture.GaussianMixture(n_components=n_components, covariance_type='full', n_init=n_init)
    clf.fit(X_train)
    if clf.converged_!=True:
        print(' !! Did not converge! Converged: ',clf.converged_)

    labels=clf.predict(X_train)

    means=[]
    stds=[]
    weights=[]
    for c in range(n_components):
        component=X_train[labels==c][:,0]
        means.append(np.mean(component))
        stds.append(np.std(component))
        weights.append(len(component)/len(data_np))

    if plot:
        gaussian = lambda x, mu, s, A: A*np.exp(-0.5*(x-mu)**2/s**2)/np.sqrt(2*np.pi*s**2)

        if len(fig_external)>0:
            fig, ax=fig_external[0], fig_external[1]
        else:
            fig, ax=plt.subplots(1, figsize=(16, 8))

        hist, bin_edges = np.histogram(data_np, bins=nbins)
        bin_size=np.diff(bin_edges)
        bin_centers = bin_edges[:-1] +  bin_size/ 2
        hist_normed = hist/(n_samples*bin_size) #normalizing to get 1 under graph
        ax.bar(bin_centers,hist_normed, bin_size, alpha=0.5)
        if len(title)>0:
            ax.set_title(title)
        else:
            ax.set_title('Histogram, '+str(n_samples)+' datapoints. ')

        #COLORMAP WITH EVENLY SPACED COLORS!
        colors=plt.cm.rainbow(np.linspace(0,1,n_components+1))#rainbow, plasma, autumn, viridis...

        x_vals=np.linspace(np.min(bin_edges), np.max(bin_edges), 500)

        g_total=np.zeros_like(x_vals)
        for c in range(n_components):
            gc=gaussian(x_vals, means[c], stds[c], weights[c])
            ax.plot(x_vals, gc, color=colors[c], linewidth=2, label='mean=%.2f'%(means[c]))
            ax.arrow(means[c], weights[c], 0, 0.1)
            g_total+=gc
        ax.plot(x_vals, g_total, color=colors[-1], linewidth=2, label='Total Model')
        plt.legend()

    if return_labels:
        return means, stds, weights, labels
    else:
        return means, stds, weights